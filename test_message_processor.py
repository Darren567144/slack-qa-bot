#!/usr/bin/env python
"""
Unit tests for MessageProcessor class.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from core.message_processor import MessageProcessor


class TestMessageProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = MessageProcessor()
    
    def test_format_message_for_llm(self):
        """Test message formatting with user context."""
        # Mock message
        msg = {
            "user": "U123456789",
            "text": "How do I deploy this?",
            "ts": "1640995200.123456"  # 2022-01-01 00:00:00
        }
        
        user_names = {"U123456789": "Alice"}
        
        result = self.processor.format_message_for_llm(msg, user_names)
        
        # Should contain timestamp, user name, and message
        self.assertIn("Alice", result)
        self.assertIn("How do I deploy this?", result)
        self.assertTrue(":" in result)  # Should have time format (HH:MM)
    
    def test_format_message_unknown_user(self):
        """Test formatting with unknown user."""
        msg = {
            "user": "U987654321",
            "text": "Test message",
            "ts": "1640995200.123456"
        }
        
        user_names = {}  # Empty user names
        
        result = self.processor.format_message_for_llm(msg, user_names)
        
        # Should use fallback user name
        self.assertIn("User4321", result)  # Last 4 digits of user ID
    
    def test_create_conversation_windows(self):
        """Test conversation window creation."""
        # Create sample messages
        messages = []
        for i in range(10):
            messages.append({
                "user": f"U{i}",
                "text": f"Message {i}",
                "ts": f"164099520{i}.123456"
            })
        
        user_names = {f"U{i}": f"User{i}" for i in range(10)}
        
        with patch.object(self.processor.config, 'CONTEXT_WINDOW_SIZE', 3):
            with patch.object(self.processor.config, 'MIN_CONVERSATION_LENGTH', 10):
                windows = self.processor.create_conversation_windows(messages, user_names)
        
        # Should create multiple windows
        self.assertGreater(len(windows), 0)
        
        # Each window should have proper structure
        for window in windows:
            self.assertIn('messages', window)
            self.assertIn('formatted_text', window)
            self.assertIn('window_start', window)
            self.assertIn('window_end', window)
    
    def test_create_conversation_windows_short_messages(self):
        """Test that short conversations are filtered out."""
        # Very short messages
        messages = [
            {"user": "U1", "text": "hi", "ts": "1640995200.1"},
            {"user": "U2", "text": "hey", "ts": "1640995200.2"}
        ]
        
        user_names = {"U1": "Alice", "U2": "Bob"}
        
        with patch.object(self.processor.config, 'MIN_CONVERSATION_LENGTH', 100):
            windows = self.processor.create_conversation_windows(messages, user_names)
        
        # Should be filtered out as too short
        self.assertEqual(len(windows), 0)


if __name__ == '__main__':
    unittest.main()