#!/usr/bin/env python
"""
Unit tests for DatabaseManager class.
"""
import unittest
import tempfile
import os
from datetime import datetime, timedelta
import json
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from database.database_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_init_database(self):
        """Test database initialization creates required tables."""
        # Database should be created and initialized
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Check statistics to verify tables exist
        stats = self.db_manager.get_statistics()
        self.assertIn('questions', stats)
        self.assertIn('answers', stats)
        self.assertIn('qa_pairs', stats)
        self.assertIn('processed_messages', stats)
    
    def test_store_qa_pair(self):
        """Test storing Q&A pairs."""
        qa_data = {
            'question': 'How do I deploy this?',
            'answer': 'Use Render or Heroku',
            'question_user': 'Alice',
            'answer_user': 'Bob',
            'channel': '#general',
            'timestamp': '2023-01-01T10:00:00',
            'confidence_score': 0.8,
            'metadata': {'test': True}
        }
        
        result_id = self.db_manager.store_qa_pair(qa_data)
        self.assertIsNotNone(result_id)
        
        # Retrieve and verify
        qa_pairs = self.db_manager.get_qa_pairs()
        self.assertEqual(len(qa_pairs), 1)
        self.assertEqual(qa_pairs[0]['question'], 'How do I deploy this?')
        self.assertEqual(qa_pairs[0]['answer'], 'Use Render or Heroku')
    
    def test_store_duplicate_qa_pair(self):
        """Test that duplicate Q&A pairs are ignored."""
        qa_data = {
            'question': 'Test question?',
            'answer': 'Test answer',
            'question_user': 'Alice',
            'answer_user': 'Bob',
            'channel': '#general'
        }
        
        # Store same pair twice
        self.db_manager.store_qa_pair(qa_data)
        self.db_manager.store_qa_pair(qa_data)
        
        # Should only have one record
        qa_pairs = self.db_manager.get_qa_pairs()
        self.assertEqual(len(qa_pairs), 1)
    
    def test_store_question(self):
        """Test storing individual questions."""
        question_data = {
            'text': 'How do I test this app?',
            'user_id': 'U123456789',
            'user_name': 'Alice',
            'channel_id': 'C123456789',
            'timestamp': datetime.now(),
            'message_ts': '1640995200.123456',
            'confidence_score': 0.9,
            'metadata': {'type': 'technical'}
        }
        
        question_id = self.db_manager.store_question(question_data)
        self.assertIsNotNone(question_id)
        
        # Verify it was stored
        stats = self.db_manager.get_statistics()
        self.assertEqual(stats['questions'], 1)
    
    def test_store_answer(self):
        """Test storing individual answers."""
        # First store a question
        question_data = {
            'text': 'How do I test this?',
            'user_id': 'U123456789',
            'user_name': 'Alice',
            'channel_id': 'C123456789',
            'timestamp': datetime.now(),
            'message_ts': '1640995200.123456',
            'confidence_score': 0.9
        }
        question_id = self.db_manager.store_question(question_data)
        
        # Then store an answer
        answer_data = {
            'text': 'Run pytest in your terminal',
            'user_id': 'U987654321',
            'user_name': 'Bob',
            'channel_id': 'C123456789',
            'timestamp': datetime.now(),
            'message_ts': '1640995300.123456',
            'confidence_score': 0.8
        }
        
        answer_id = self.db_manager.store_answer(answer_data, question_id)
        self.assertIsNotNone(answer_id)
        
        stats = self.db_manager.get_statistics()
        self.assertEqual(stats['answers'], 1)
    
    def test_find_recent_questions(self):
        """Test finding recent unanswered questions."""
        # Store a recent question
        recent_question = {
            'text': 'Recent question?',
            'user_name': 'Alice',
            'channel_id': 'C123456789',
            'timestamp': datetime.now(),
            'message_ts': '1640995200.123456',
            'confidence_score': 0.8
        }
        self.db_manager.store_question(recent_question)
        
        # Store an old question
        old_question = {
            'text': 'Old question?',
            'user_name': 'Bob',
            'channel_id': 'C123456789',
            'timestamp': datetime.now() - timedelta(days=2),
            'message_ts': '1640895200.123456',
            'confidence_score': 0.8
        }
        self.db_manager.store_question(old_question)
        
        # Find recent questions (within 24 hours)
        recent = self.db_manager.find_recent_questions('C123456789', hours=24)
        
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]['text'], 'Recent question?')
    
    def test_message_processing_tracking(self):
        """Test message processing tracking."""
        message_ts = '1640995200.123456'
        channel_id = 'C123456789'
        
        # Initially not processed
        self.assertFalse(self.db_manager.is_message_processed(message_ts))
        
        # Mark as processed
        self.db_manager.mark_message_processed(message_ts, channel_id)
        
        # Now should be processed
        self.assertTrue(self.db_manager.is_message_processed(message_ts))
    
    def test_get_qa_pairs_with_channel_filter(self):
        """Test retrieving Q&A pairs with channel filtering."""
        # Store pairs in different channels
        qa1 = {
            'question': 'Question 1?',
            'answer': 'Answer 1',
            'channel': '#general'
        }
        qa2 = {
            'question': 'Question 2?',
            'answer': 'Answer 2',
            'channel': '#dev'
        }
        
        self.db_manager.store_qa_pair(qa1)
        self.db_manager.store_qa_pair(qa2)
        
        # Get all pairs
        all_pairs = self.db_manager.get_qa_pairs()
        self.assertEqual(len(all_pairs), 2)
        
        # Get pairs from specific channel
        general_pairs = self.db_manager.get_qa_pairs(channel='#general')
        self.assertEqual(len(general_pairs), 1)
        self.assertEqual(general_pairs[0]['question'], 'Question 1?')
    
    def test_get_statistics(self):
        """Test database statistics."""
        # Store some test data
        self.db_manager.store_qa_pair({
            'question': 'Test?',
            'answer': 'Test answer',
            'channel': '#general'
        })
        
        question_data = {
            'text': 'Another question?',
            'channel_id': 'C123456789',
            'timestamp': datetime.now(),
            'message_ts': '1640995200.123456'
        }
        self.db_manager.store_question(question_data)
        
        self.db_manager.mark_message_processed('1640995200.123456', 'C123456789')
        
        stats = self.db_manager.get_statistics()
        
        self.assertEqual(stats['qa_pairs'], 1)
        self.assertEqual(stats['questions'], 1)
        self.assertEqual(stats['processed_messages'], 1)
        self.assertIn('database_path', stats)
    
    def test_export_to_csv(self):
        """Test CSV export functionality."""
        # Store test data
        qa_data = {
            'question': 'How to export?',
            'answer': 'Use CSV export',
            'question_user': 'Alice',
            'answer_user': 'Bob',
            'channel': '#general',
            'timestamp': '2023-01-01T10:00:00'
        }
        self.db_manager.store_qa_pair(qa_data)
        
        # Export to temporary CSV file
        temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp_csv.close()
        
        try:
            self.db_manager.export_to_csv(temp_csv.name)
            
            # Verify file was created and has content
            self.assertTrue(os.path.exists(temp_csv.name))
            with open(temp_csv.name, 'r') as f:
                content = f.read()
                self.assertIn('How to export?', content)
                self.assertIn('Use CSV export', content)
        finally:
            if os.path.exists(temp_csv.name):
                os.unlink(temp_csv.name)


if __name__ == '__main__':
    unittest.main()