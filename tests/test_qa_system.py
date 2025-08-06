#!/usr/bin/env python
"""
Comprehensive test suite for the Q&A detection and storage system.
"""
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Set test environment before importing our modules
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['SLACK_TOKEN'] = 'test-token'
os.environ['SLACK_APP_TOKEN'] = 'test-app-token'

from database_manager import DatabaseManager
from openai_analyzer import OpenAIAnalyzer
from config_manager import PipelineConfig


class TestDatabaseManager(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        Path(self.temp_db.name).unlink(missing_ok=True)
    
    def test_database_initialization(self):
        """Test database tables are created properly."""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            
            # Check all tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['questions', 'answers', 'qa_pairs', 'processed_messages']
            for table in expected_tables:
                self.assertIn(table, tables, f"Table {table} not found")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(questions)")
            columns = [row[1] for row in cursor.fetchall()]
            self.assertIn('text', columns)
            self.assertIn('user_id', columns)
            self.assertIn('message_ts', columns)
    
    def test_store_qa_pair(self):
        """Test storing Q&A pairs."""
        qa_data = {
            'question': 'How do I test this?',
            'answer': 'Run the test suite',
            'question_user': 'Alice',
            'answer_user': 'Bob',
            'channel': 'test-channel',
            'timestamp': datetime.now().isoformat(),
            'confidence_score': 0.9
        }
        
        qa_id = self.db_manager.store_qa_pair(qa_data)
        self.assertIsInstance(qa_id, int)
        
        # Verify stored data
        pairs = self.db_manager.get_qa_pairs(channel='test-channel')
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]['question'], 'How do I test this?')
        self.assertEqual(pairs[0]['answer'], 'Run the test suite')
    
    def test_store_question_and_answer(self):
        """Test storing questions and linked answers."""
        question_data = {
            'text': 'What is the meaning of life?',
            'user_id': 'U123',
            'user_name': 'Deep Thought',
            'channel_id': 'C456',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.123456',
            'confidence_score': 0.95
        }
        
        question_id = self.db_manager.store_question(question_data)
        self.assertIsInstance(question_id, int)
        
        answer_data = {
            'text': '42',
            'user_id': 'U789',
            'user_name': 'Computer',
            'channel_id': 'C456',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.789012',
            'confidence_score': 0.85
        }
        
        answer_id = self.db_manager.store_answer(answer_data, question_id)
        self.assertIsInstance(answer_id, int)
    
    def test_find_recent_questions(self):
        """Test finding recent unanswered questions."""
        # Store a question
        question_data = {
            'text': 'How do I deploy this?',
            'user_id': 'U123',
            'user_name': 'Developer',
            'channel_id': 'C456',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.111111',
            'confidence_score': 0.8
        }
        
        question_id = self.db_manager.store_question(question_data)
        
        # Find recent questions
        recent = self.db_manager.find_recent_questions('C456', hours=1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]['text'], 'How do I deploy this?')
        
        # Store an answer to the question
        answer_data = {
            'text': 'Use docker compose up',
            'user_id': 'U789',
            'user_name': 'DevOps',
            'channel_id': 'C456',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.222222',
            'confidence_score': 0.9
        }
        
        self.db_manager.store_answer(answer_data, question_id)
        
        # Should not find it anymore since it's answered
        recent = self.db_manager.find_recent_questions('C456', hours=1)
        self.assertEqual(len(recent), 0)
    
    def test_message_processing_tracking(self):
        """Test message processing tracking."""
        message_ts = '1234567890.123456'
        channel_id = 'C789'
        
        # Initially not processed
        self.assertFalse(self.db_manager.is_message_processed(message_ts))
        
        # Mark as processed
        self.db_manager.mark_message_processed(message_ts, channel_id)
        
        # Should now be processed
        self.assertTrue(self.db_manager.is_message_processed(message_ts))
    
    def test_statistics(self):
        """Test database statistics."""
        # Store some test data
        qa_data = {
            'question': 'Test question?',
            'answer': 'Test answer',
            'question_user': 'User1',
            'answer_user': 'User2',
            'channel': 'test-channel',
            'timestamp': datetime.now().isoformat()
        }
        
        self.db_manager.store_qa_pair(qa_data)
        
        stats = self.db_manager.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('qa_pairs', stats)
        self.assertEqual(stats['qa_pairs'], 1)
        self.assertIn('database_path', stats)
    
    def test_export_to_csv(self):
        """Test CSV export functionality."""
        # Store test data
        qa_data = {
            'question': 'Export test?',
            'answer': 'Yes, it works',
            'question_user': 'Tester',
            'answer_user': 'System',
            'channel': 'export-test',
            'timestamp': datetime.now().isoformat()
        }
        
        self.db_manager.store_qa_pair(qa_data)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_csv = f.name
        
        try:
            self.db_manager.export_to_csv(temp_csv)
            
            # Verify file exists and has content
            self.assertTrue(Path(temp_csv).exists())
            with open(temp_csv, 'r') as f:
                content = f.read()
                self.assertIn('Export test?', content)
                self.assertIn('Yes, it works', content)
        finally:
            Path(temp_csv).unlink(missing_ok=True)


class TestOpenAIAnalyzer(unittest.TestCase):
    """Test OpenAI analyzer functions."""
    
    def setUp(self):
        """Set up analyzer with mocked OpenAI."""
        self.analyzer = OpenAIAnalyzer()
    
    @patch('openai.chat.completions.create')
    def test_is_question_detection(self, mock_openai):
        """Test question detection."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"is_question": true, "confidence": 0.9, "question_type": "direct"}'
        mock_openai.return_value = mock_response
        
        result = self.analyzer.is_question("How do I set up this feature?")
        
        self.assertTrue(result['is_question'])
        self.assertEqual(result['confidence'], 0.9)
        self.assertEqual(result['question_type'], 'direct')
    
    @patch('openai.chat.completions.create')
    def test_answer_detection(self, mock_openai):
        """Test answer detection."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"is_answer": true, "confidence": 0.8, "answer_quality": "direct"}'
        mock_openai.return_value = mock_response
        
        result = self.analyzer.is_answer_to_question(
            "How do I deploy?", 
            "Use docker compose up"
        )
        
        self.assertTrue(result['is_answer'])
        self.assertEqual(result['confidence'], 0.8)
        self.assertEqual(result['answer_quality'], 'direct')
    
    @patch('openai.chat.completions.create')
    def test_conversation_analysis(self, mock_openai):
        """Test full conversation Q&A extraction."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''[
            {
                "question": "How do I test this?",
                "answer": "Run pytest",
                "question_user": "Alice",
                "answer_user": "Bob"
            }
        ]'''
        mock_openai.return_value = mock_response
        
        conversation = """
        [10:00] Alice: How do I test this?
        [10:01] Bob: Run pytest
        """
        
        result = self.analyzer.extract_qa_pairs_from_conversation(conversation)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['question'], "How do I test this?")
        self.assertEqual(result[0]['answer'], "Run pytest")
    
    @patch('openai.chat.completions.create')
    def test_openai_error_handling(self, mock_openai):
        """Test error handling when OpenAI fails."""
        mock_openai.side_effect = Exception("API Error")
        
        result = self.analyzer.is_question("Test question?")
        
        self.assertFalse(result['is_question'])
        self.assertEqual(result['confidence'], 0.0)
    
    @patch('openai.chat.completions.create')
    def test_invalid_json_handling(self, mock_openai):
        """Test handling of invalid JSON responses."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Invalid JSON response'
        mock_openai.return_value = mock_response
        
        result = self.analyzer.is_question("Test question?")
        
        self.assertFalse(result['is_question'])
        self.assertEqual(result['confidence'], 0.0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up integration test environment."""
        Path(self.temp_db.name).unlink(missing_ok=True)
    
    def test_full_qa_workflow(self):
        """Test complete Q&A detection and storage workflow."""
        # Simulate question detection
        question_data = {
            'text': 'How do I configure SSL?',
            'user_id': 'U123',
            'user_name': 'WebDev',
            'channel_id': 'C456',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.111',
            'confidence_score': 0.92
        }
        
        question_id = self.db_manager.store_question(question_data)
        
        # Verify question was stored
        recent_questions = self.db_manager.find_recent_questions('C456')
        self.assertEqual(len(recent_questions), 1)
        self.assertEqual(recent_questions[0]['id'], question_id)
        
        # Simulate answer detection
        answer_data = {
            'text': 'Use nginx with Let\'s Encrypt certificates',
            'user_id': 'U789',
            'user_name': 'SysAdmin',
            'channel_id': 'C456',
            'timestamp': datetime.now(),
            'message_ts': '1234567890.222',
            'confidence_score': 0.88
        }
        
        answer_id = self.db_manager.store_answer(answer_data, question_id)
        
        # Verify answer was linked to question
        self.assertIsInstance(answer_id, int)
        
        # Check that question is no longer in recent unanswered questions
        recent_questions = self.db_manager.find_recent_questions('C456')
        self.assertEqual(len(recent_questions), 0)
        
        # Store as Q&A pair for compatibility
        qa_pair = {
            'question': question_data['text'],
            'answer': answer_data['text'],
            'question_user': question_data['user_name'],
            'answer_user': answer_data['user_name'],
            'channel': 'C456',
            'timestamp': datetime.now().isoformat(),
            'confidence_score': min(question_data['confidence_score'], answer_data['confidence_score'])
        }
        
        qa_id = self.db_manager.store_qa_pair(qa_pair)
        
        # Verify Q&A pair was stored
        pairs = self.db_manager.get_qa_pairs('C456')
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]['question'], 'How do I configure SSL?')
    
    def test_concurrent_message_processing(self):
        """Test handling multiple messages concurrently."""
        # Simulate multiple messages being processed
        messages = [
            {
                'text': f'Question {i}?',
                'user_id': f'U{i}',
                'user_name': f'User{i}',
                'channel_id': 'C123',
                'timestamp': datetime.now(),
                'message_ts': f'123456789.{i:03d}',
                'confidence_score': 0.8
            }
            for i in range(5)
        ]
        
        # Store all questions
        question_ids = []
        for msg in messages:
            qid = self.db_manager.store_question(msg)
            question_ids.append(qid)
            
            # Mark message as processed
            self.db_manager.mark_message_processed(msg['message_ts'], msg['channel_id'])
        
        # Verify all were stored
        self.assertEqual(len(question_ids), 5)
        
        # Verify all messages marked as processed
        for msg in messages:
            self.assertTrue(self.db_manager.is_message_processed(msg['message_ts']))
        
        # Verify recent questions
        recent = self.db_manager.find_recent_questions('C123')
        self.assertEqual(len(recent), 5)
    
    def test_data_consistency(self):
        """Test data consistency across operations."""
        # Store a Q&A pair
        qa_data = {
            'question': 'What is Docker?',
            'answer': 'Docker is a containerization platform',
            'question_user': 'Newbie',
            'answer_user': 'Expert',
            'channel': 'general',
            'timestamp': datetime.now().isoformat(),
            'confidence_score': 0.95
        }
        
        self.db_manager.store_qa_pair(qa_data)
        
        # Get statistics
        stats = self.db_manager.get_statistics()
        self.assertEqual(stats['qa_pairs'], 1)
        
        # Export and verify data integrity
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_csv = f.name
        
        try:
            self.db_manager.export_to_csv(temp_csv)
            
            with open(temp_csv, 'r') as f:
                content = f.read()
                self.assertIn('What is Docker?', content)
                self.assertIn('Docker is a containerization platform', content)
                self.assertIn('Newbie', content)
                self.assertIn('Expert', content)
        finally:
            Path(temp_csv).unlink(missing_ok=True)


def run_all_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestOpenAIAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_all_tests()
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")