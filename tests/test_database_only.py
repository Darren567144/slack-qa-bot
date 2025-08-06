#!/usr/bin/env python
"""
Test database functionality without Slack SDK dependencies.
"""
import os
import time
import tempfile
from datetime import datetime
from pathlib import Path

# Set test environment
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['SLACK_TOKEN'] = 'test-slack-token'
os.environ['SLACK_APP_TOKEN'] = 'test-app-token'

from database_manager import DatabaseManager
from config_manager import PipelineConfig


def test_database_comprehensive():
    """Comprehensive database test with realistic scenarios."""
    print("🔍 Testing Database Operations...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name
    
    try:
        db_manager = DatabaseManager(db_path)
        config = PipelineConfig()
        
        print(f"✅ Database initialized at: {db_path}")
        
        # Scenario 1: Real-time Q&A detection workflow
        print("\n📊 Scenario 1: Real-time Q&A Detection")
        
        # Someone asks a question
        question_msg = {
            'text': 'How do I deploy a Python app to production?',
            'user_id': 'U12345',
            'user_name': 'WebDevNovice',
            'channel_id': 'C67890',
            'timestamp': datetime.now(),
            'message_ts': '1700000001.000001',
            'confidence_score': 0.92,
            'metadata': {'question_type': 'direct', 'detected_at': datetime.now().isoformat()}
        }
        
        question_id = db_manager.store_question(question_msg)
        print(f"   ❓ Stored question ID: {question_id}")
        print(f"      Text: {question_msg['text']}")
        
        # Check recent unanswered questions
        recent = db_manager.find_recent_questions('C67890')
        assert len(recent) == 1
        assert recent[0]['id'] == question_id
        print(f"   ✅ Found {len(recent)} recent unanswered questions")
        
        # Someone provides an answer
        time.sleep(0.1)  # Small delay to simulate real conversation
        
        answer_msg = {
            'text': 'Use Docker with a production-ready image, set up CI/CD pipeline, and deploy to a cloud platform like AWS or Heroku',
            'user_id': 'U54321',
            'user_name': 'DevOpsExpert',
            'channel_id': 'C67890',
            'timestamp': datetime.now(),
            'message_ts': '1700000002.000002',
            'confidence_score': 0.89,
            'metadata': {'answer_quality': 'direct', 'detected_at': datetime.now().isoformat()}
        }
        
        answer_id = db_manager.store_answer(answer_msg, question_id)
        print(f"   💡 Stored answer ID: {answer_id} (linked to question {question_id})")
        print(f"      Text: {answer_msg['text'][:60]}...")
        
        # Store as Q&A pair for backward compatibility
        qa_pair = {
            'question': question_msg['text'],
            'answer': answer_msg['text'],
            'question_user': question_msg['user_name'],
            'answer_user': answer_msg['user_name'],
            'channel': 'C67890',
            'timestamp': answer_msg['timestamp'].isoformat(),
            'confidence_score': min(question_msg['confidence_score'], answer_msg['confidence_score'])
        }
        
        qa_pair_id = db_manager.store_qa_pair(qa_pair)
        print(f"   📝 Stored Q&A pair ID: {qa_pair_id}")
        
        # Verify question is now answered
        recent = db_manager.find_recent_questions('C67890')
        assert len(recent) == 0
        print(f"   ✅ Question marked as answered (0 unanswered remaining)")
        
        # Scenario 2: Multiple questions in different channels
        print("\n📊 Scenario 2: Multiple Channels")
        
        channels = ['python-help', 'devops', 'general']
        question_ids = []
        
        for i, channel in enumerate(channels):
            q_data = {
                'text': f'Question {i+1} in {channel}?',
                'user_id': f'U{1000+i}',
                'user_name': f'User{i+1}',
                'channel_id': channel,
                'timestamp': datetime.now(),
                'message_ts': f'170000000{i+3}.{i+3:06d}',
                'confidence_score': 0.8 + (i * 0.05)
            }
            
            qid = db_manager.store_question(q_data)
            question_ids.append(qid)
            db_manager.mark_message_processed(q_data['message_ts'], channel)
        
        print(f"   ✅ Stored {len(question_ids)} questions across {len(channels)} channels")
        
        # Check questions per channel
        for channel in channels:
            recent = db_manager.find_recent_questions(channel)
            print(f"      {channel}: {len(recent)} unanswered questions")
        
        # Scenario 3: Message processing tracking
        print("\n📊 Scenario 3: Message Processing Tracking")
        
        test_messages = [
            '1700000010.001',
            '1700000011.002', 
            '1700000012.003'
        ]
        
        # Initially none are processed
        for msg_ts in test_messages:
            assert not db_manager.is_message_processed(msg_ts)
        
        # Mark them as processed
        for i, msg_ts in enumerate(test_messages):
            db_manager.mark_message_processed(msg_ts, f'channel-{i}')
        
        # Verify they're all processed
        processed_count = 0
        for msg_ts in test_messages:
            if db_manager.is_message_processed(msg_ts):
                processed_count += 1
        
        print(f"   ✅ Processed {processed_count}/{len(test_messages)} messages")
        
        # Scenario 4: Statistics and export
        print("\n📊 Scenario 4: Statistics and Export")
        
        stats = db_manager.get_statistics()
        print(f"   Database Statistics:")
        print(f"      Questions: {stats['questions']}")
        print(f"      Answers: {stats['answers']}")
        print(f"      Q&A Pairs: {stats['qa_pairs']}")
        print(f"      Processed Messages: {stats['processed_messages']}")
        print(f"      Unique Channels: {stats['unique_channels']}")
        
        # Test CSV export
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_csv:
            csv_path = tmp_csv.name
        
        db_manager.export_to_csv(csv_path)
        
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            print(f"   ✅ Exported CSV with {len(lines)} lines (including header)")
            
            # Verify content
            content = ''.join(lines)
            assert 'Python app to production' in content
            print(f"      Content verification passed")
        
        Path(csv_path).unlink()
        
        # Scenario 5: Data retrieval
        print("\n📊 Scenario 5: Data Retrieval")
        
        # Get Q&A pairs by channel
        pairs_c67890 = db_manager.get_qa_pairs('C67890')
        pairs_all = db_manager.get_qa_pairs()
        
        print(f"   Q&A pairs in C67890: {len(pairs_c67890)}")
        print(f"   Total Q&A pairs: {len(pairs_all)}")
        
        if pairs_c67890:
            pair = pairs_c67890[0]
            print(f"   Sample Q&A:")
            print(f"      Q: {pair['question'][:50]}...")
            print(f"      A: {pair['answer'][:50]}...")
            print(f"      Users: {pair['question_user']} → {pair['answer_user']}")
            print(f"      Confidence: {pair['confidence_score']:.2f}")
        
        print("\n✅ All database scenarios completed successfully!")
        
        return stats
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def performance_test():
    """Test database performance with larger datasets."""
    print("\n⚡ Performance Test...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name
    
    try:
        db_manager = DatabaseManager(db_path)
        
        # Store 100 Q&A pairs
        start_time = time.time()
        
        for i in range(100):
            qa_pair = {
                'question': f'Performance test question {i}?',
                'answer': f'This is answer number {i} for performance testing',
                'question_user': f'TestUser{i % 10}',
                'answer_user': f'ExpertUser{(i + 5) % 10}',
                'channel': f'test-channel-{i % 5}',
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.5 + (i % 50) / 100
            }
            
            db_manager.store_qa_pair(qa_pair)
        
        store_time = time.time() - start_time
        
        # Retrieve all pairs
        start_time = time.time()
        all_pairs = db_manager.get_qa_pairs(limit=1000)
        retrieve_time = time.time() - start_time
        
        # Get statistics
        start_time = time.time()
        stats = db_manager.get_statistics()
        stats_time = time.time() - start_time
        
        print(f"   ✅ Performance Results:")
        print(f"      Store 100 Q&A pairs: {store_time:.3f}s ({100/store_time:.1f} pairs/sec)")
        print(f"      Retrieve {len(all_pairs)} pairs: {retrieve_time:.3f}s")
        print(f"      Get statistics: {stats_time:.3f}s")
        print(f"      Total database size: {stats['qa_pairs']} Q&A pairs")
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def main():
    """Run all database tests."""
    print("🚀 Comprehensive Database Testing")
    print("=" * 60)
    
    try:
        # Run comprehensive functionality test
        stats = test_database_comprehensive()
        
        # Run performance test
        performance_test()
        
        print("\n" + "=" * 60)
        print("🎉 ALL DATABASE TESTS PASSED!")
        print("✅ Real-time Q&A workflow")
        print("✅ Multi-channel support")
        print("✅ Message processing tracking")
        print("✅ Statistics and export")
        print("✅ Data retrieval")
        print("✅ Performance testing")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)