#!/usr/bin/env python
"""
Unit tests for OpenAIAnalyzer class.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from core.openai_analyzer import OpenAIAnalyzer


class TestOpenAIAnalyzer(unittest.TestCase):
    
    def setUp(self):
        with patch('core.openai_analyzer.get_required_env_vars') as mock_env:
            mock_env.return_value = {'OPENAI_API_KEY': 'test-key'}
            self.analyzer = OpenAIAnalyzer()
    
    @patch('openai.chat.completions.create')
    def test_extract_qa_pairs_success(self, mock_create):
        """Test successful Q&A extraction."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            {
                "question": "How do I deploy this app?",
                "answer": "You can deploy it using Render or Heroku",
                "question_user": "Alice",
                "answer_user": "Bob"
            }
        ])
        mock_create.return_value = mock_response
        
        conversation = "[10:00] Alice: How do I deploy this app?\n[10:01] Bob: You can deploy it using Render or Heroku"
        
        result = self.analyzer.extract_qa_pairs_from_conversation(conversation)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['question'], "How do I deploy this app?")
        self.assertEqual(result[0]['answer'], "You can deploy it using Render or Heroku")
    
    @patch('openai.chat.completions.create')
    def test_extract_qa_pairs_with_markdown(self, mock_create):
        """Test Q&A extraction with markdown code blocks."""
        # Mock OpenAI response with markdown
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```json\n[]\n```"
        mock_create.return_value = mock_response
        
        conversation = "[10:00] Alice: Just saying hello"
        
        result = self.analyzer.extract_qa_pairs_from_conversation(conversation)
        
        self.assertEqual(result, [])
    
    @patch('openai.chat.completions.create')
    def test_extract_qa_pairs_invalid_json(self, mock_create):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_create.return_value = mock_response
        
        conversation = "[10:00] Alice: Test message"
        
        result = self.analyzer.extract_qa_pairs_from_conversation(conversation)
        
        self.assertEqual(result, [])
    
    @patch('openai.chat.completions.create')
    def test_extract_qa_pairs_api_error(self, mock_create):
        """Test handling of API errors."""
        mock_create.side_effect = Exception("API Error")
        
        conversation = "[10:00] Alice: Test message"
        
        result = self.analyzer.extract_qa_pairs_from_conversation(conversation)
        
        self.assertEqual(result, [])
    
    @patch('openai.chat.completions.create')
    def test_is_question_direct(self, mock_create):
        """Test direct question detection."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_question": True,
            "confidence": 0.95,
            "question_type": "direct"
        })
        mock_create.return_value = mock_response
        
        result = self.analyzer.is_question("How do I install this?")
        
        self.assertTrue(result['is_question'])
        self.assertEqual(result['confidence'], 0.95)
        self.assertEqual(result['question_type'], 'direct')
    
    @patch('openai.chat.completions.create')
    def test_is_question_implicit(self, mock_create):
        """Test implicit question detection."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_question": True,
            "confidence": 0.80,
            "question_type": "implicit"
        })
        mock_create.return_value = mock_response
        
        result = self.analyzer.is_question("I need help with deployment")
        
        self.assertTrue(result['is_question'])
        self.assertEqual(result['confidence'], 0.80)
    
    @patch('openai.chat.completions.create')
    def test_is_question_not_question(self, mock_create):
        """Test non-question detection."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_question": False,
            "confidence": 0.95,
            "question_type": "none"
        })
        mock_create.return_value = mock_response
        
        result = self.analyzer.is_question("I deployed the app successfully")
        
        self.assertFalse(result['is_question'])
        self.assertEqual(result['question_type'], 'none')
    
    @patch('openai.chat.completions.create')
    def test_is_answer_to_question_direct(self, mock_create):
        """Test direct answer detection."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_answer": True,
            "confidence": 0.90,
            "answer_quality": "direct"
        })
        mock_create.return_value = mock_response
        
        result = self.analyzer.is_answer_to_question(
            "How do I deploy this?",
            "Use the command 'render deploy'"
        )
        
        self.assertTrue(result['is_answer'])
        self.assertEqual(result['confidence'], 0.90)
        self.assertEqual(result['answer_quality'], 'direct')
    
    @patch('openai.chat.completions.create')
    def test_is_answer_to_question_irrelevant(self, mock_create):
        """Test irrelevant answer detection."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_answer": False,
            "confidence": 0.85,
            "answer_quality": "irrelevant"
        })
        mock_create.return_value = mock_response
        
        result = self.analyzer.is_answer_to_question(
            "How do I deploy this?",
            "I had lunch today"
        )
        
        self.assertFalse(result['is_answer'])
        self.assertEqual(result['answer_quality'], 'irrelevant')
    
    @patch('openai.chat.completions.create')
    def test_question_analysis_json_error(self, mock_create):
        """Test question analysis with JSON parsing error."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_create.return_value = mock_response
        
        result = self.analyzer.is_question("Test question?")
        
        # Should return default values
        self.assertFalse(result['is_question'])
        self.assertEqual(result['confidence'], 0.0)
        self.assertEqual(result['question_type'], 'none')


if __name__ == '__main__':
    unittest.main()