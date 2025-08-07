#!/usr/bin/env python3
"""
Quick test to verify Slack connection works.
This tests your tokens without needing OpenAI API.
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_slack_connection():
    """Test if we can connect to Slack with the provided tokens."""
    print("🔍 Testing Slack Connection...")
    print("=" * 40)
    
    # Check environment variables
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    app_token = os.getenv('SLACK_APP_TOKEN')
    
    if not bot_token:
        print("❌ SLACK_BOT_TOKEN not found in environment")
        return False
        
    if not app_token:
        print("❌ SLACK_APP_TOKEN not found in environment") 
        return False
        
    print(f"✅ SLACK_BOT_TOKEN: {bot_token[:20]}...")
    print(f"✅ SLACK_APP_TOKEN: {app_token[:20]}...")
    
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
        
        print("\n🔗 Testing Slack Web Client connection...")
        client = WebClient(token=bot_token)
        
        # Test API connection
        response = client.auth_test()
        print(f"✅ Connected to Slack!")
        print(f"   Bot User: @{response['user']}")
        print(f"   Team: {response['team']}")
        print(f"   User ID: {response['user_id']}")
        
        return True
        
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        if e.response['error'] == 'invalid_auth':
            print("   → Check your SLACK_BOT_TOKEN is correct")
        return False
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_socket_mode_setup():
    """Test if Socket Mode can be initialized."""
    print("\n🔌 Testing Socket Mode setup...")
    
    try:
        from slack_bolt import App
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        
        bot_token = os.getenv('SLACK_BOT_TOKEN')
        app_token = os.getenv('SLACK_APP_TOKEN')
        
        # Create Slack app
        app = App(token=bot_token)
        
        # Test socket mode handler creation (don't start it)
        handler = SocketModeHandler(app, app_token)
        print("✅ Socket Mode handler created successfully")
        print("✅ Ready for real-time message processing")
        
        return True
        
    except Exception as e:
        print(f"❌ Socket Mode Error: {e}")
        return False

def main():
    """Run connection tests."""
    print("🚀 Slack Bot Connection Test")
    print("=" * 40)
    
    # Test 1: Basic connection
    if not test_slack_connection():
        print("\n❌ Slack connection failed. Check your tokens.")
        return
        
    # Test 2: Socket mode setup
    if not test_socket_mode_setup():
        print("\n❌ Socket Mode setup failed.")
        return
        
    print("\n" + "=" * 40)
    print("🎉 All connection tests passed!")
    print("✅ Your Slack tokens are working correctly")
    print("✅ Socket Mode is configured properly")
    print("✅ Ready to test the full bot!")
    print("\n💡 Next: Add OpenAI API key and run: python3 start.py")

if __name__ == "__main__":
    main()