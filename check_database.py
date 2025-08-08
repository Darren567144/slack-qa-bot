#!/usr/bin/env python
"""
Script to check what's stored in the PostgreSQL database.
"""
import os
from database.production_database import ProductionDatabaseManager

def main():
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("Set it with: export DATABASE_URL='your_postgres_url'")
        return
    
    print(f"🔍 Connecting to database...")
    db = ProductionDatabaseManager(database_url)
    
    # Get statistics
    print("\n📊 Database Statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Check scanned channels
    try:
        if hasattr(db, 'get_scanned_channels'):
            scanned = db.get_scanned_channels()
            print(f"\n✅ Scanned Channels: {len(scanned)}")
            for channel_id in scanned:
                print(f"   - {channel_id}")
        else:
            print("\n⚠️  Scanned channels method not available")
    except Exception as e:
        print(f"\n❌ Error checking scanned channels: {e}")
    
    # Get recent questions
    try:
        recent_qa = db.get_qa_pairs(limit=5)
        print(f"\n❓ Recent Q&A Pairs ({len(recent_qa)}):")
        for i, qa in enumerate(recent_qa, 1):
            print(f"   {i}. Q: {qa['question'][:60]}...")
            print(f"      A: {qa['answer'][:60]}...")
            print(f"      Channel: {qa['channel']}")
            print()
    except Exception as e:
        print(f"\n❌ Error getting Q&A pairs: {e}")

if __name__ == "__main__":
    main()