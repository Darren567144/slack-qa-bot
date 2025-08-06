#!/usr/bin/env python
"""
Message processing and formatting utilities.
"""
from datetime import datetime
from config.config_manager import PipelineConfig


class MessageProcessor:
    """Handles message processing and formatting for LLM analysis."""
    
    def __init__(self):
        self.config = PipelineConfig()
    
    def format_message_for_llm(self, msg, user_names):
        """Format message with user context for LLM."""
        user_id = msg.get("user", "unknown")
        user_name = user_names.get(user_id, f"User{user_id[-4:] if user_id != 'unknown' else 'Unknown'}")
        text = msg.get("text", "").strip()
        timestamp = datetime.fromtimestamp(float(msg["ts"])).strftime("%H:%M")
        
        return f"[{timestamp}] {user_name}: {text}"
    
    def create_conversation_windows(self, messages, user_names):
        """Create larger, non-overlapping conversation windows for analysis."""
        windows = []
        
        # Process in larger, non-overlapping chunks to reduce API calls
        chunk_size = self.config.CONTEXT_WINDOW_SIZE
        
        for i in range(0, len(messages), chunk_size):
            window_messages = messages[i:i + chunk_size]
            
            # Format for LLM
            formatted_messages = [self.format_message_for_llm(msg, user_names) for msg in window_messages]
            conversation_text = "\n".join(formatted_messages)
            
            # Skip short conversations
            if len(formatted_messages) < 3 or len(conversation_text.strip()) < self.config.MIN_CONVERSATION_LENGTH:
                continue
            
            windows.append({
                'messages': window_messages,
                'formatted_text': conversation_text,
                'window_start': i,
                'window_end': i + len(window_messages) - 1
            })
        
        return windows