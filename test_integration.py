#!/usr/bin/env python
"""
Integration tests for the complete Q&A pipeline.
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import json
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from core.message_processor import MessageProcessor
from core.openai_analyzer import OpenAIAnalyzer
from database.database_manager import DatabaseManager


class TestQAPipeline(unittest.TestCase):
    """Integration tests for the complete Q&A detection and storage pipeline."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.message_processor = MessageProcessor()
        
        # Mock OpenAI analyzer to avoid API calls
        with patch('core.openai_analyzer.get_required_env_vars') as mock_env:
            mock_env.return_value = {'OPENAI_API_KEY': 'test-key'}
            self.openai_analyzer = OpenAIAnalyzer()
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @patch('openai.chat.completions.create')
    def test_complete_qa_detection_pipeline(self, mock_openai):
        """Test the complete pipeline from messages to stored Q&A pairs."""
        # Sample conversation messages
        messages = [
            {
                "user": "U123456789",
                "text": "Hey everyone, how do I deploy this app to production?",
                "ts": "1640995200.123456"
            },
            {
                "user": "U987654321", 
                "text": "You can use Render or Heroku. Both support Python apps.",
                "ts": "1640995260.123456"
            },
            {
                "user": "U123456789",
                "text": "Thanks! Which one is cheaper?",
                "ts": "1640995320.123456"
            },
            {
                "user": "U987654321",
                "text": "Render has a more generous free tier. I'd recommend starting there.",
                "ts": "1640995380.123456"
            }
        ]
        
        user_names = {
            "U123456789": "Alice",
            "U987654321": "Bob"
        }
        
        # Mock OpenAI responses for Q&A extraction
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            {
                "question": "how do I deploy this app to production?",
                "answer": "You can use Render or Heroku. Both support Python apps.",
                "question_user": "Alice",
                "answer_user": "Bob"
            },
            {
                "question": "Which one is cheaper?",
                "answer": "Render has a more generous free tier. I'd recommend starting there.",
                "question_user": "Alice", 
                "answer_user": "Bob"
            }
        ])
        mock_openai.return_value = mock_response
        
        # Process messages through pipeline
        # 1. Create conversation windows
        windows = self.message_processor.create_conversation_windows(messages, user_names)
        self.assertGreater(len(windows), 0)
        
        # 2. Extract Q&A pairs using OpenAI
        all_qa_pairs = []
        for window in windows:
            qa_pairs = self.openai_analyzer.extract_qa_pairs_from_conversation(window['formatted_text'])
            all_qa_pairs.extend(qa_pairs)
        
        # Should have extracted 2 Q&A pairs
        self.assertEqual(len(all_qa_pairs), 2)
        
        # 3. Store in database
        stored_count = 0
        for qa_pair in all_qa_pairs:
            qa_data = {
                'question': qa_pair['question'],
                'answer': qa_pair['answer'],
                'question_user': qa_pair['question_user'],
                'answer_user': qa_pair['answer_user'],
                'channel': '#general',
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.8
            }
            self.db_manager.store_qa_pair(qa_data)
            stored_count += 1
        
        # 4. Verify storage
        retrieved_pairs = self.db_manager.get_qa_pairs()
        self.assertEqual(len(retrieved_pairs), 2)
        
        # Verify content
        questions = [pair['question'] for pair in retrieved_pairs]
        self.assertIn("how do I deploy this app to production?", questions)
        self.assertIn("Which one is cheaper?", questions)
        
        # Verify statistics
        stats = self.db_manager.get_statistics()
        self.assertEqual(stats['qa_pairs'], 2)
    
    @patch('openai.chat.completions.create')
    def test_real_time_question_answer_matching(self, mock_openai):
        """Test real-time question detection and answer matching."""
        channel_id = "C123456789"
        
        # Mock OpenAI responses for individual message analysis
        def mock_openai_side_effect(*args, **kwargs):
            messages = kwargs['messages']
            user_message = messages[-1]['content']
            
            # Check if this is a question analysis or answer analysis call
            system_message = messages[0]['content'] if messages else ""
            
            if "question seeking information" in system_message.lower():
                # This is a question detection call
                if "how do i test" in user_message.lower() or "test this application" in user_message.lower():
                    response = MagicMock()
                    response.choices[0].message.content = json.dumps({
                        "is_question": True,
                        "confidence": 0.9,
                        "question_type": "direct"
                    })
                    return response
                else:
                    response = MagicMock()
                    response.choices[0].message.content = json.dumps({
                        "is_question": False,
                        "confidence": 0.1,
                        "question_type": "none"
                    })
                    return response
            elif "answer addresses the given question" in system_message.lower():
                # This is an answer detection call
                if "run pytest" in user_message.lower():
                    response = MagicMock()
                    response.choices[0].message.content = json.dumps({
                        "is_answer": True,
                        "confidence": 0.85,
                        "answer_quality": "direct"
                    })
                    return response
                else:
                    response = MagicMock()
                    response.choices[0].message.content = json.dumps({
                        "is_answer": False,
                        "confidence": 0.1,
                        "answer_quality": "irrelevant"
                    })
                    return response
            else:
                # Default fallback
                response = MagicMock()
                response.choices[0].message.content = json.dumps({
                    "is_question": False,
                    "confidence": 0.1,
                    "question_type": "none"
                })
                return response
        
        mock_openai.side_effect = mock_openai_side_effect
        
        # Simulate real-time message processing
        # 1. Question arrives
        question_data = {
            'text': 'How do I test this application?',
            'user_id': 'U123456789',
            'user_name': 'Alice',
            'channel_id': channel_id,
            'timestamp': datetime.now(),
            'message_ts': '1640995200.123456',
            'confidence_score': 0.9
        }
        
        # Analyze if it's a question
        question_analysis = self.openai_analyzer.is_question(question_data['text'])
        self.assertTrue(question_analysis['is_question'])
        question_data['confidence_score'] = question_analysis['confidence']
        
        # Store the question
        question_id = self.db_manager.store_question(question_data)
        self.assertIsNotNone(question_id)
        
        # 2. Answer arrives later
        answer_data = {
            'text': 'Run pytest in your terminal to execute all tests',
            'user_id': 'U987654321',
            'user_name': 'Bob',
            'channel_id': channel_id,
            'timestamp': datetime.now(),
            'message_ts': '1640995300.123456'
        }
        
        # Find recent questions to match against
        recent_questions = self.db_manager.find_recent_questions(channel_id)
        self.assertEqual(len(recent_questions), 1)
        
        # Analyze if the answer matches any recent questions
        best_match_question = recent_questions[0]
        answer_analysis = self.openai_analyzer.is_answer_to_question(
            best_match_question['text'],
            answer_data['text']
        )
        
        self.assertTrue(answer_analysis['is_answer'])
        answer_data['confidence_score'] = answer_analysis['confidence']
        
        # Store the linked answer
        answer_id = self.db_manager.store_answer(answer_data, best_match_question['id'])
        self.assertIsNotNone(answer_id)
        
        # 3. Verify the complete Q&A pair was created
        # After linking, the question should no longer appear in "recent unanswered"
        unanswered_questions = self.db_manager.find_recent_questions(channel_id)
        self.assertEqual(len(unanswered_questions), 0)  # Should be empty now
        
        # Verify database statistics
        stats = self.db_manager.get_statistics()
        self.assertEqual(stats['questions'], 1)
        self.assertEqual(stats['answers'], 1)
    
    @patch('openai.chat.completions.create')
    def test_duplicate_prevention(self, mock_openai):
        """Test that duplicate Q&A pairs are prevented."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            {
                "question": "What is Python?",
                "answer": "Python is a programming language",
                "question_user": "Alice",
                "answer_user": "Bob"
            }
        ])
        mock_openai.return_value = mock_response
        
        qa_data = {
            'question': 'What is Python?',
            'answer': 'Python is a programming language',
            'question_user': 'Alice',
            'answer_user': 'Bob',
            'channel': '#general',
            'timestamp': datetime.now().isoformat(),
            'confidence_score': 0.8
        }
        
        # Store the same Q&A pair twice
        id1 = self.db_manager.store_qa_pair(qa_data)
        id2 = self.db_manager.store_qa_pair(qa_data)
        
        # Should only have one record
        pairs = self.db_manager.get_qa_pairs()
        self.assertEqual(len(pairs), 1)
        
        # Verify statistics
        stats = self.db_manager.get_statistics()
        self.assertEqual(stats['qa_pairs'], 1)
    
    def test_message_processing_tracking(self):
        """Test that processed messages are tracked to avoid reprocessing."""
        channel_id = "C123456789"
        message_ts = "1640995200.123456"
        
        # Initially not processed
        self.assertFalse(self.db_manager.is_message_processed(message_ts))
        
        # Process and mark
        self.db_manager.mark_message_processed(message_ts, channel_id)
        
        # Should now be marked as processed
        self.assertTrue(self.db_manager.is_message_processed(message_ts))
        
        # Verify statistics
        stats = self.db_manager.get_statistics()
        self.assertEqual(stats['processed_messages'], 1)
    
    def test_export_functionality(self):
        """Test data export functionality."""
        # Store test data
        qa_data = {
            'question': 'How to export data?',
            'answer': 'Use the export_to_csv method',
            'question_user': 'Alice',
            'answer_user': 'Bot',
            'channel': '#testing',
            'timestamp': datetime.now().isoformat(),
            'confidence_score': 0.9
        }
        
        self.db_manager.store_qa_pair(qa_data)
        
        # Export to temporary file
        temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp_csv.close()
        
        try:
            self.db_manager.export_to_csv(temp_csv.name)
            
            # Verify export
            self.assertTrue(os.path.exists(temp_csv.name))
            with open(temp_csv.name, 'r') as f:
                content = f.read()
                self.assertIn('How to export data?', content)
                self.assertIn('Use the export_to_csv method', content)
        finally:
            if os.path.exists(temp_csv.name):
                os.unlink(temp_csv.name)


if __name__ == '__main__':
    unittest.main()