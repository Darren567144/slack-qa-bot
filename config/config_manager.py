#!/usr/bin/env python
"""
Configuration and environment management for the Slack Q&A pipeline.
"""
import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        # Remove quotes and inline comments
                        value = value.split('#')[0].strip()
                        value = value.strip('"').strip("'")
                        if key and value:
                            os.environ[key] = value


def get_required_env_vars():
    """Get required environment variables with validation."""
    load_env()
    
    # Support both bot token and user token
    slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
    slack_user_token = os.environ.get('SLACK_USER_TOKEN')
    
    # Prefer user token if available (more autonomous access)
    slack_token = slack_user_token if slack_user_token else slack_bot_token
    
    required_vars = {
        'SLACK_TOKEN': slack_token,
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'SLACK_APP_TOKEN': os.environ.get('SLACK_APP_TOKEN')  # For Socket Mode
    }
    
    # Add token type for logging
    if slack_user_token:
        required_vars['TOKEN_TYPE'] = 'USER_TOKEN'
    elif slack_bot_token:
        required_vars['TOKEN_TYPE'] = 'BOT_TOKEN'
    else:
        required_vars['TOKEN_TYPE'] = 'NONE'
    
    missing_vars = [var for var, value in required_vars.items() if not value and var != 'TOKEN_TYPE']
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return required_vars


class PipelineConfig:
    """Configuration settings for the pipeline."""
    
    def __init__(self):
        self.OUTPUT_DIR = Path("./out")
        self.MAX_MESSAGES_PER_CHANNEL = 200  # Increased from 50
        self.CONTEXT_WINDOW_SIZE = 25      # Larger windows = fewer OpenAI calls
        self.MIN_CONVERSATION_LENGTH = 50
        self.MIN_ANSWER_LENGTH = 10
        self.OPENAI_MODEL = "gpt-4o-mini"
        self.OPENAI_MAX_TOKENS = 1000
        self.OPENAI_TEMPERATURE = 0.1
        
        # Optimized for Slack rate limits
        self.SLACK_API_BATCH_SIZE = 200  # Max messages per request (Slack limit)
        self.SLACK_API_DELAY = 0.8       # More aggressive: 0.8s = ~75 requests/minute
        self.SLACK_USERS_BATCH_DELAY = 0.3  # More aggressive: 0.3s = ~200 requests/minute
        
        # Rate limit recovery settings
        self.RATE_LIMIT_RETRY_DELAY = 60  # Default retry delay when rate limited
        self.RATE_LIMIT_BACKOFF_MULTIPLIER = 1.5  # Exponential backoff
        
        # Real-time processing configuration
        self.REALTIME_ENABLED = True
        self.MESSAGE_BUFFER_SIZE = 10  # Number of recent messages to keep in memory per channel
        self.QUESTION_DETECTION_THRESHOLD = 0.7  # Confidence threshold for question detection
        self.ANSWER_DETECTION_THRESHOLD = 0.6   # Confidence threshold for answer detection
        self.ANSWER_TIMEOUT_HOURS = 24  # How long to wait for answers to questions
        self.PROCESS_MESSAGE_DELAY = 2.0  # Delay before processing new messages (avoid editing)
        
        # Database configuration - use persistent storage if available
        database_path = os.environ.get('DATABASE_PATH')
        if database_path:
            self.DATABASE_PATH = Path(database_path)
            # Ensure the directory exists
            self.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.DATABASE_PATH = self.OUTPUT_DIR / "qa_database.db"
        
        # Ensure output directory exists
        self.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)