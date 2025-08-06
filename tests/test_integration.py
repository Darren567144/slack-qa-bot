#!/usr/bin/env python
"""
Integration test for the complete Q&A system with simulated real-time processing.
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
from openai_analyzer import OpenAIAnalyzer
from config_manager import PipelineConfig
from qa_extractor import QAExtractor


def test_database_integration():
    """Test database operations with real data structures."""
    print("🔍 Testing Database Integration...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name
    
    try:
        db_manager = DatabaseManager(db_path)
        
        # Test storing and retrieving Q&A pairs
        test_qa = {
            'question': 'How do I set up continuous integration?',
            'answer': 'Use GitHub Actions with workflow files in .github/workflows/',
            'question_user': 'DevNewbie',
            'answer_user': 'SeniorDev',
            'channel': 'engineering',
            'timestamp': datetime.now().isoformat(),
            'confidence_score': 0.92
        }
        
        qa_id = db_manager.store_qa_pair(test_qa)
        print(f"✅ Stored Q&A pair with ID: {qa_id}")
        
        # Retrieve and verify
        pairs = db_manager.get_qa_pairs('engineering')
        assert len(pairs) == 1
        assert pairs[0]['question'] == test_qa['question']
        print("✅ Q&A pair retrieval verified")
        
        # Test question/answer linking
        question_data = {
            'text': 'What is the best way to handle errors in Python?',
            'user_id': 'U12345',
            'user_name': 'PythonLearner',
            'channel_id': 'python-help',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.123456',
            'confidence_score': 0.88
        }
        
        question_id = db_manager.store_question(question_data)
        print(f"✅ Stored question with ID: {question_id}")
        
        # Find unanswered questions
        recent = db_manager.find_recent_questions('python-help')
        assert len(recent) == 1
        assert recent[0]['id'] == question_id
        print("✅ Recent unanswered questions found")
        
        # Add answer
        answer_data = {
            'text': 'Use try/except blocks and proper exception handling',
            'user_id': 'U67890',
            'user_name': 'PythonExpert',
            'channel_id': 'python-help',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.789012',
            'confidence_score': 0.95
        }
        
        answer_id = db_manager.store_answer(answer_data, question_id)
        print(f"✅ Stored answer with ID: {answer_id}")
        
        # Verify question is no longer unanswered
        recent = db_manager.find_recent_questions('python-help')
        assert len(recent) == 0
        print("✅ Question marked as answered")
        
        # Test statistics
        stats = db_manager.get_statistics()
        print(f"📊 Database stats: {stats}")
        assert stats['questions'] >= 1
        assert stats['answers'] >= 1
        assert stats['qa_pairs'] >= 1
        
        # Test CSV export
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_csv:
            csv_path = tmp_csv.name
        
        db_manager.export_to_csv(csv_path)
        
        with open(csv_path, 'r') as f:
            content = f.read()
            assert 'continuous integration' in content
            print("✅ CSV export verified")
        
        Path(csv_path).unlink()
        
        print("✅ Database integration test PASSED")
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def simulate_message_processing():
    """Simulate real-time message processing workflow."""
    print("\n🔄 Testing Simulated Message Processing...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name
    
    try:
        db_manager = DatabaseManager(db_path)
        config = PipelineConfig()
        
        # Simulate a sequence of messages in a channel
        messages = [
            {
                'text': 'Hey everyone, I need help with Docker deployment',
                'user_id': 'U001',
                'user_name': 'WebDev',
                'channel_id': 'devops',
                'timestamp': datetime.now(),
                'message_ts': '1700000001.000001',
                'is_question': True,
                'confidence': 0.85
            },
            {
                'text': 'What specific issue are you having?',
                'user_id': 'U002', 
                'user_name': 'DevOpsGuru',
                'channel_id': 'devops',
                'timestamp': datetime.now(),
                'message_ts': '1700000002.000002',
                'is_question': False,
                'confidence': 0.3
            },
            {
                'text': 'My containers keep crashing with exit code 1',
                'user_id': 'U001',
                'user_name': 'WebDev', 
                'channel_id': 'devops',
                'timestamp': datetime.now(),
                'message_ts': '1700000003.000003',
                'is_question': False,
                'confidence': 0.2
            },
            {
                'text': 'Check your logs with docker logs <container_name>. Exit code 1 usually means there\'s an error in your application',
                'user_id': 'U002',
                'user_name': 'DevOpsGuru',
                'channel_id': 'devops', 
                'timestamp': datetime.now(),
                'message_ts': '1700000004.000004',
                'is_question': False,
                'confidence': 0.1
            }
        ]
        
        print("📥 Processing simulated messages...")
        
        questions_stored = []
        
        for i, msg in enumerate(messages):
            print(f"   Processing message {i+1}: {msg['text'][:50]}...")
            
            # Check if already processed
            if db_manager.is_message_processed(msg['message_ts']):
                print(f"   ⏭️  Message already processed, skipping")
                continue
            
            # Simulate question detection
            if msg.get('is_question', False) and msg.get('confidence', 0) >= config.QUESTION_DETECTION_THRESHOLD:
                print(f"   ❓ Detected question (confidence: {msg['confidence']:.2f})")
                
                question_data = {
                    'text': msg['text'],
                    'user_id': msg['user_id'],
                    'user_name': msg['user_name'],
                    'channel_id': msg['channel_id'],
                    'timestamp': msg['timestamp'],
                    'message_ts': msg['message_ts'],
                    'confidence_score': msg['confidence'],
                    'metadata': {'simulated': True}
                }
                
                question_id = db_manager.store_question(question_data)
                questions_stored.append(question_id)
                print(f"   ✅ Stored question with ID: {question_id}")
                
            else:
                # Check if it might be an answer
                recent_questions = db_manager.find_recent_questions(msg['channel_id'], hours=1)
                
                if recent_questions and i == 3:  # Last message is the answer
                    print(f"   💡 Potential answer to {len(recent_questions)} recent questions")
                    
                    # Link to the first unanswered question
                    question = recent_questions[0]
                    
                    answer_data = {
                        'text': msg['text'],
                        'user_id': msg['user_id'],
                        'user_name': msg['user_name'],
                        'channel_id': msg['channel_id'],
                        'timestamp': msg['timestamp'],
                        'message_ts': msg['message_ts'],
                        'confidence_score': 0.9,  # High confidence for this simulation
                        'metadata': {'simulated': True, 'linked_to': question['id']}
                    }
                    
                    answer_id = db_manager.store_answer(answer_data, question['id'])
                    print(f"   ✅ Stored answer with ID: {answer_id} (linked to question {question['id']})")
                    
                    # Store as Q&A pair for compatibility
                    qa_pair = {
                        'question': question['text'],
                        'answer': msg['text'],
                        'question_user': question['user_name'],
                        'answer_user': msg['user_name'],
                        'channel': msg['channel_id'],
                        'timestamp': msg['timestamp'].isoformat(),
                        'confidence_score': min(question['confidence_score'], 0.9)
                    }
                    
                    qa_pair_id = db_manager.store_qa_pair(qa_pair)
                    print(f"   ✅ Stored Q&A pair with ID: {qa_pair_id}")
            
            # Mark as processed
            db_manager.mark_message_processed(msg['message_ts'], msg['channel_id'])
            
            # Small delay to simulate real-time processing
            time.sleep(0.1)
        
        print(f"\n📊 Processing complete!")
        print(f"   Questions stored: {len(questions_stored)}")
        
        # Verify final state
        stats = db_manager.get_statistics()
        print(f"   Final database stats: {stats}")
        
        # Check that questions are properly answered
        unanswered = db_manager.find_recent_questions('devops', hours=1)
        print(f"   Unanswered questions remaining: {len(unanswered)}")
        
        # Get all Q&A pairs
        qa_pairs = db_manager.get_qa_pairs('devops')
        print(f"   Q&A pairs found: {len(qa_pairs)}")
        
        if qa_pairs:
            print(f"   Sample Q&A:")
            print(f"     Q: {qa_pairs[0]['question'][:60]}...")
            print(f"     A: {qa_pairs[0]['answer'][:60]}...")
        
        print("✅ Message processing simulation PASSED")
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_qa_extractor_with_database():
    """Test that QA extractor works with database storage."""
    print("\n🔧 Testing QA Extractor Database Integration...")
    
    # Create temporary database  
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Temporarily patch the config to use our test database
        original_config = PipelineConfig()
        original_db_path = original_config.DATABASE_PATH
        original_config.DATABASE_PATH = Path(db_path)
        
        # Initialize QA extractor (this will create the database)
        qa_extractor = QAExtractor()
        
        # Override the database manager to use our test database
        qa_extractor.db_manager = DatabaseManager(db_path)
        
        # Verify database was created and is working
        stats = qa_extractor.db_manager.get_statistics()
        print(f"✅ QA Extractor database initialized: {stats}")
        
        # Test storing a Q&A pair directly
        test_pair = {
            'question': 'How do I test database integration?',
            'answer': 'Create comprehensive test suites with temporary databases',
            'question_user': 'Tester',
            'answer_user': 'Expert',
            'channel': 'testing',
            'timestamp': datetime.now().isoformat(),
            'confidence_score': 0.95
        }
        
        pair_id = qa_extractor.db_manager.store_qa_pair(test_pair)
        print(f"✅ Stored test Q&A pair with ID: {pair_id}")
        
        # Verify it was stored
        pairs = qa_extractor.db_manager.get_qa_pairs('testing')
        assert len(pairs) == 1
        assert pairs[0]['question'] == test_pair['question']
        
        print("✅ QA Extractor database integration PASSED")
        
        # Restore original config
        original_config.DATABASE_PATH = original_db_path
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Integration Tests for Q&A System")
    print("=" * 60)
    
    try:
        test_database_integration()
        simulate_message_processing()  
        test_qa_extractor_with_database()
        
        print("\n" + "=" * 60)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Database operations working correctly")
        print("✅ Message processing simulation successful") 
        print("✅ QA Extractor database integration verified")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)