#!/usr/bin/env python
"""
Database usage examples for the Q&A detection and storage system.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set minimal environment for database operations
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
os.environ.setdefault('SLACK_TOKEN', 'test-token')
os.environ.setdefault('SLACK_APP_TOKEN', 'test-app-token')

# Try cloud database manager first, fallback to SQLite
try:
    from database.cloud_database_manager import CloudDatabaseManager as DatabaseManager
    print("📊 Using CloudDatabaseManager (PostgreSQL/SQLite support)")
except ImportError as e:
    print(f"⚠️  Cloud database dependencies not available: {e}")
    print("📊 Falling back to SQLite DatabaseManager")
    from database.database_manager import DatabaseManager

from config.config_manager import PipelineConfig


def example_basic_operations():
    """Example of basic database operations."""
    print("📊 Example: Basic Database Operations")
    print("-" * 40)
    
    # Initialize database
    db_manager = DatabaseManager("./out/example_qa.db")
    
    # Store a Q&A pair (backward compatibility with existing system)
    qa_pair = {
        'question': 'How do I handle environment variables in Python?',
        'answer': 'Use os.environ.get("VAR_NAME") or python-dotenv for .env files',
        'question_user': 'PythonLearner',
        'answer_user': 'PythonExpert',
        'channel': 'python-help',
        'timestamp': datetime.now().isoformat(),
        'confidence_score': 0.92
    }
    
    qa_id = db_manager.store_qa_pair(qa_pair)
    print(f"✅ Stored Q&A pair with ID: {qa_id}")
    
    # Store individual question (new real-time system)
    question_data = {
        'text': 'What is the best way to structure a FastAPI project?',
        'user_id': 'U123456',
        'user_name': 'WebDeveloper',
        'channel_id': 'fastapi-help',
        'timestamp': datetime.now(),
        'message_ts': '1700000001.123456',
        'confidence_score': 0.88,
        'metadata': {
            'question_type': 'direct',
            'detected_at': datetime.now().isoformat()
        }
    }
    
    question_id = db_manager.store_question(question_data)
    print(f"✅ Stored question with ID: {question_id}")
    
    # Store corresponding answer
    answer_data = {
        'text': 'Use a directory structure with app/, models/, routes/, and services/ folders',
        'user_id': 'U789012',
        'user_name': 'FastAPIExpert',
        'channel_id': 'fastapi-help',
        'timestamp': datetime.now(),
        'message_ts': '1700000002.789012',
        'confidence_score': 0.95,
        'metadata': {
            'answer_quality': 'direct',
            'detected_at': datetime.now().isoformat()
        }
    }
    
    answer_id = db_manager.store_answer(answer_data, question_id)
    print(f"✅ Stored answer with ID: {answer_id} (linked to question {question_id})")
    
    return db_manager


def example_data_retrieval(db_manager):
    """Example of data retrieval operations."""
    print("\n🔍 Example: Data Retrieval")
    print("-" * 40)
    
    # Get statistics
    stats = db_manager.get_statistics()
    print(f"📈 Database contains:")
    print(f"   Questions: {stats['questions']}")
    print(f"   Answers: {stats['answers']}")
    print(f"   Q&A Pairs: {stats['qa_pairs']}")
    print(f"   Processed Messages: {stats['processed_messages']}")
    print(f"   Unique Channels: {stats['unique_channels']}")
    
    # Find recent unanswered questions
    unanswered = db_manager.find_recent_questions('python-help', hours=24)
    print(f"\n❓ Found {len(unanswered)} unanswered questions in python-help")
    
    unanswered_fastapi = db_manager.find_recent_questions('fastapi-help', hours=24)
    print(f"❓ Found {len(unanswered_fastapi)} unanswered questions in fastapi-help")
    
    # Get all Q&A pairs
    all_pairs = db_manager.get_qa_pairs()
    print(f"\n📝 Retrieved {len(all_pairs)} Q&A pairs:")
    
    for i, pair in enumerate(all_pairs):
        print(f"   {i+1}. Q: {pair['question'][:50]}...")
        print(f"      A: {pair['answer'][:50]}...")
        print(f"      Users: {pair['question_user']} → {pair['answer_user']}")
        print(f"      Channel: {pair['channel']}")
        print(f"      Confidence: {pair['confidence_score']:.2f}")
        print()
    
    # Get pairs from specific channel
    python_pairs = db_manager.get_qa_pairs('python-help')
    print(f"📝 Q&A pairs in python-help channel: {len(python_pairs)}")


def example_message_tracking(db_manager):
    """Example of message processing tracking."""
    print("\n📥 Example: Message Processing Tracking")
    print("-" * 40)
    
    # Simulate processing some messages
    test_messages = [
        {'ts': '1700000010.001', 'channel': 'general'},
        {'ts': '1700000011.002', 'channel': 'python-help'},
        {'ts': '1700000012.003', 'channel': 'devops'},
    ]
    
    print("Processing messages:")
    for msg in test_messages:
        # Check if already processed
        if db_manager.is_message_processed(msg['ts']):
            print(f"   ⏭️  Message {msg['ts']} already processed")
        else:
            # Mark as processed
            db_manager.mark_message_processed(msg['ts'], msg['channel'])
            print(f"   ✅ Processed message {msg['ts']} in {msg['channel']}")
    
    # Try processing the same messages again
    print("\nTrying to process same messages again:")
    for msg in test_messages:
        if db_manager.is_message_processed(msg['ts']):
            print(f"   ⏭️  Message {msg['ts']} already processed (skipped)")
        else:
            print(f"   🆕 Message {msg['ts']} not processed yet")


def example_export_operations(db_manager):
    """Example of export operations."""
    print("\n📤 Example: Export Operations")
    print("-" * 40)
    
    # Export Q&A pairs to CSV
    csv_file = "./out/example_qa_pairs.csv"
    db_manager.export_to_csv(csv_file, table='qa_pairs')
    print(f"✅ Exported Q&A pairs to {csv_file}")
    
    # Check the exported file
    if Path(csv_file).exists():
        with open(csv_file, 'r') as f:
            lines = f.readlines()
            print(f"   📄 CSV file contains {len(lines)} lines (including header)")
            if len(lines) > 1:
                print(f"   📝 Sample content: {lines[1][:80]}...")
    
    # Export questions to CSV
    questions_csv = "./out/example_questions.csv"
    db_manager.export_to_csv(questions_csv, table='questions')
    print(f"✅ Exported questions to {questions_csv}")


def example_realistic_workflow(db_manager):
    """Example of a realistic Q&A workflow."""
    print("\n🔄 Example: Realistic Q&A Workflow")
    print("-" * 40)
    
    # Simulate a conversation in a DevOps channel
    print("Simulating DevOps channel conversation...")
    
    # Step 1: Someone asks a question
    question_1 = {
        'text': 'How do I set up auto-scaling for my Kubernetes deployment?',
        'user_id': 'U001',
        'user_name': 'DevOpsBeginner',
        'channel_id': 'devops',
        'timestamp': datetime.now(),
        'message_ts': '1700100001.001',
        'confidence_score': 0.92,
        'metadata': {'question_type': 'technical', 'topic': 'kubernetes'}
    }
    
    q1_id = db_manager.store_question(question_1)
    db_manager.mark_message_processed(question_1['message_ts'], question_1['channel_id'])
    print(f"   ❓ Question 1 stored (ID: {q1_id}): {question_1['text'][:50]}...")
    
    # Step 2: Another question comes in
    question_2 = {
        'text': 'What\'s the difference between HPA and VPA in Kubernetes?',
        'user_id': 'U002',
        'user_name': 'CloudEngineer',
        'channel_id': 'devops',
        'timestamp': datetime.now(),
        'message_ts': '1700100002.002',
        'confidence_score': 0.88,
        'metadata': {'question_type': 'conceptual', 'topic': 'kubernetes'}
    }
    
    q2_id = db_manager.store_question(question_2)
    db_manager.mark_message_processed(question_2['message_ts'], question_2['channel_id'])
    print(f"   ❓ Question 2 stored (ID: {q2_id}): {question_2['text'][:50]}...")
    
    # Step 3: Expert provides answer to first question
    answer_1 = {
        'text': 'Use Horizontal Pod Autoscaler (HPA) with CPU/memory metrics. Create an HPA resource that targets your deployment.',
        'user_id': 'U003',
        'user_name': 'K8sExpert',
        'channel_id': 'devops',
        'timestamp': datetime.now(),
        'message_ts': '1700100003.003',
        'confidence_score': 0.95,
        'metadata': {'answer_quality': 'comprehensive', 'expertise_level': 'expert'}
    }
    
    a1_id = db_manager.store_answer(answer_1, q1_id)
    db_manager.mark_message_processed(answer_1['message_ts'], answer_1['channel_id'])
    print(f"   💡 Answer 1 stored (ID: {a1_id}): {answer_1['text'][:50]}...")
    
    # Store as Q&A pair for compatibility
    qa_pair_1 = {
        'question': question_1['text'],
        'answer': answer_1['text'],
        'question_user': question_1['user_name'],
        'answer_user': answer_1['user_name'],
        'channel': 'devops',
        'timestamp': answer_1['timestamp'].isoformat(),
        'confidence_score': min(question_1['confidence_score'], answer_1['confidence_score'])
    }
    
    qa1_id = db_manager.store_qa_pair(qa_pair_1)
    print(f"   📝 Q&A pair 1 stored (ID: {qa1_id})")
    
    # Step 4: Same expert answers second question  
    answer_2 = {
        'text': 'HPA scales pods horizontally (more replicas), VPA scales vertically (more resources per pod). Use HPA for stateless apps, VPA for resource optimization.',
        'user_id': 'U003',
        'user_name': 'K8sExpert',
        'channel_id': 'devops',
        'timestamp': datetime.now(),
        'message_ts': '1700100004.004',
        'confidence_score': 0.93,
        'metadata': {'answer_quality': 'comprehensive', 'expertise_level': 'expert'}
    }
    
    a2_id = db_manager.store_answer(answer_2, q2_id)
    db_manager.mark_message_processed(answer_2['message_ts'], answer_2['channel_id'])
    print(f"   💡 Answer 2 stored (ID: {a2_id}): {answer_2['text'][:50]}...")
    
    # Store as Q&A pair for compatibility
    qa_pair_2 = {
        'question': question_2['text'],
        'answer': answer_2['text'],
        'question_user': question_2['user_name'],
        'answer_user': answer_2['user_name'],
        'channel': 'devops',
        'timestamp': answer_2['timestamp'].isoformat(),
        'confidence_score': min(question_2['confidence_score'], answer_2['confidence_score'])
    }
    
    qa2_id = db_manager.store_qa_pair(qa_pair_2)
    print(f"   📝 Q&A pair 2 stored (ID: {qa2_id})")
    
    # Step 5: Check the results
    print("\n📊 Workflow Results:")
    unanswered = db_manager.find_recent_questions('devops')
    print(f"   Unanswered questions in devops: {len(unanswered)}")
    
    devops_pairs = db_manager.get_qa_pairs('devops')
    print(f"   Q&A pairs in devops channel: {len(devops_pairs)}")
    
    stats = db_manager.get_statistics()
    print(f"   Total database: {stats['questions']} questions, {stats['answers']} answers")


def main():
    """Run all database examples."""
    print("🚀 Q&A Database System - Usage Examples")
    print("=" * 60)
    
    try:
        # Ensure output directory exists
        Path("./out").mkdir(exist_ok=True)
        
        # Run examples
        db_manager = example_basic_operations()
        example_data_retrieval(db_manager)
        example_message_tracking(db_manager)
        example_export_operations(db_manager)
        example_realistic_workflow(db_manager)
        
        print("\n" + "=" * 60)
        print("🎉 All examples completed successfully!")
        print("✅ Basic database operations")
        print("✅ Data retrieval and queries")
        print("✅ Message processing tracking")
        print("✅ Export operations")
        print("✅ Realistic Q&A workflow")
        
        print(f"\n📁 Database created at: {db_manager.db_path}")
        print("   You can explore it with any SQLite browser")
        print("   Or query it directly with Python/SQL")
        
        # Show final statistics
        final_stats = db_manager.get_statistics()
        print(f"\n📊 Final Database Statistics:")
        for key, value in final_stats.items():
            if key != 'database_path':
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()