#!/usr/bin/env python
"""
Render.com startup script for Slack Q&A Bot.
This is what Render runs to start your bot 24/7.
"""
import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging for cloud deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check that all required environment variables are set."""
    required_vars = [
        'SLACK_BOT_TOKEN',      # xoxb-...
        'SLACK_APP_TOKEN',      # xapp-... 
        'OPENAI_API_KEY'        # sk-...
        # DATABASE_URL is automatically provided by Render PostgreSQL
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        logger.error("Set these in Render dashboard → Settings → Environment Variables")
        return False
    
    logger.info("✅ All required environment variables found")
    return True

def main():
    """Start the Slack Q&A bot."""
    try:
        logger.info("🚀 Starting Slack Q&A Bot on Render...")
        
        # Check environment
        if not check_environment():
            sys.exit(1)
            
        # Check database connection
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            logger.info(f"🐘 Using PostgreSQL database: {database_url[:50]}...")
        else:
            logger.info("📁 No DATABASE_URL found, will use SQLite fallback")
        
        # Import and start the bot
        logger.info("🔄 Initializing real-time Q&A monitor...")
        from realtime_monitor import RealtimeQAMonitor
        
        monitor = RealtimeQAMonitor()
        logger.info("🎯 Starting real-time monitoring (press Ctrl+C to stop)...")
        
        # This runs indefinitely
        monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()