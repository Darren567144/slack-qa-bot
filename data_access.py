#!/usr/bin/env python
"""
Simple data access utilities for your QA bot database.
Use this to view and export your Q&A data.
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.database_manager import DatabaseManager

def show_database_stats():
    """Show database statistics."""
    try:
        db = DatabaseManager()
        stats = db.get_statistics()
        
        print("📊 Database Statistics:")
        print(f"   📁 Location: {stats['database_path']}")
        print(f"   ❓ Questions: {stats['questions']}")
        print(f"   💬 Answers: {stats['answers']}")
        print(f"   🔄 Q&A Pairs: {stats['qa_pairs']}")
        print(f"   📨 Processed Messages: {stats['processed_messages']}")
        print(f"   📺 Unique Channels: {stats['unique_channels']}")
        
        return stats
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return None

def show_recent_qa_pairs(limit=10):
    """Show recent Q&A pairs."""
    try:
        db = DatabaseManager()
        pairs = db.get_qa_pairs(limit=limit)
        
        print(f"\n🔍 Recent {len(pairs)} Q&A Pairs:")
        print("=" * 50)
        
        for i, pair in enumerate(pairs, 1):
            print(f"\n{i}. 📍 Channel: {pair['channel']}")
            print(f"   ❓ Q: {pair['question'][:80]}...")
            print(f"   💬 A: {pair['answer'][:80]}...")
            print(f"   👤 {pair['question_user']} → {pair['answer_user']}")
            print(f"   🕐 {pair['timestamp']}")
        
        return pairs
    except Exception as e:
        print(f"❌ Error retrieving Q&A pairs: {e}")
        return []

def export_all_data():
    """Export all data to CSV."""
    try:
        db = DatabaseManager()
        
        # Export Q&A pairs
        qa_file = "qa_pairs_export.csv"
        db.export_to_csv(qa_file, table='qa_pairs')
        print(f"✅ Q&A pairs exported to: {qa_file}")
        
        # Export questions  
        questions_file = "questions_export.csv"
        db.export_to_csv(questions_file, table='questions')
        print(f"✅ Questions exported to: {questions_file}")
        
        return qa_file, questions_file
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return None, None

def main():
    """Run data access commands."""
    print("🤖 QA Bot Data Access Tool")
    print("=" * 30)
    
    # Show stats
    stats = show_database_stats()
    
    if stats and stats['qa_pairs'] > 0:
        # Show recent pairs
        show_recent_qa_pairs(5)
        
        # Export data
        print("\n📤 Exporting data...")
        export_all_data()
    else:
        print("\n💡 No Q&A pairs found yet. Try using your bot in Slack first!")

if __name__ == "__main__":
    main()