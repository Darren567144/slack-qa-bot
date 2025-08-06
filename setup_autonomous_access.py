#!/usr/bin/env python
"""
Setup script for autonomous Slack bot access.
This script helps you configure your bot for autonomous channel access.
"""
import os
from pathlib import Path
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

def check_env_file():
    """Check if .env file exists and show current configuration."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("📄 Found existing .env file:")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if 'TOKEN' in key:
                            # Show masked token
                            masked_value = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
                            print(f"   {key}={masked_value}")
                        else:
                            print(f"   {key}={value}")
    else:
        print("❌ No .env file found")
    
    print()

def test_current_tokens():
    """Test current token configuration."""
    print("🔍 Testing current token configuration...")
    
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    user_token = os.environ.get("SLACK_USER_TOKEN")
    
    if bot_token:
        print("✅ SLACK_BOT_TOKEN found")
        test_token_access(bot_token, "BOT_TOKEN")
    else:
        print("❌ SLACK_BOT_TOKEN not found")
    
    if user_token:
        print("✅ SLACK_USER_TOKEN found")
        test_token_access(user_token, "USER_TOKEN")
    else:
        print("❌ SLACK_USER_TOKEN not found")
    
    print()

def test_token_access(token, token_type):
    """Test what channels a token can access."""
    try:
        client = WebClient(token=token)
        auth_resp = client.auth_test()
        
        # Test channel access
        public_resp = client.conversations_list(types="public_channel", limit=100)
        public_channels = public_resp["channels"]
        accessible_public = [ch for ch in public_channels if ch.get("is_member", False)]
        
        private_resp = client.conversations_list(types="private_channel", limit=100)
        private_channels = private_resp["channels"]
        accessible_private = [ch for ch in private_channels if ch.get("is_member", False)]
        
        total_accessible = len(accessible_public) + len(accessible_private)
        
        print(f"   📊 {token_type} can access {total_accessible} channels:")
        print(f"      - Public: {len(accessible_public)}")
        print(f"      - Private: {len(accessible_private)}")
        
        return total_accessible
        
    except SlackApiError as e:
        print(f"   ❌ {token_type} error: {e}")
        return 0

def generate_env_template():
    """Generate a template .env file."""
    env_template = """# Slack Bot Configuration
# Choose ONE of the following token types:

# Option 1: User Token (Recommended for autonomous access)
# Get this from: https://api.slack.com/apps -> Your App -> OAuth & Permissions -> User OAuth Token
SLACK_USER_TOKEN=xoxp-your-user-token-here

# Option 2: Bot Token (Limited access, requires manual invitations)
# Get this from: https://api.slack.com/apps -> Your App -> OAuth & Permissions -> Bot User OAuth Token
# SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# OpenAI API Key (required for Q&A analysis)
OPENAI_API_KEY=your-openai-api-key-here
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists. Backing up to .env.backup")
        env_file.rename(".env.backup")
    
    with open(".env", "w") as f:
        f.write(env_template)
    
    print("✅ Created .env template file")
    print("📝 Please edit .env with your actual tokens")

def show_setup_instructions():
    """Show detailed setup instructions."""
    print("\n🚀 SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("\n1️⃣  CREATE SLACK APP (if you haven't already):")
    print("   - Go to https://api.slack.com/apps")
    print("   - Click 'Create New App'")
    print("   - Choose 'From scratch'")
    print("   - Name your app (e.g., 'QA Bot')")
    print("   - Select your workspace")
    
    print("\n2️⃣  CONFIGURE PERMISSIONS:")
    print("   - Go to 'OAuth & Permissions' in your app")
    print("   - Under 'Scopes', add these permissions:")
    print("     • channels:read")
    print("     • groups:read") 
    print("     • channels:history")
    print("     • users:read")
    print("   - Click 'Install to Workspace'")
    
    print("\n3️⃣  GET YOUR TOKEN:")
    print("   - After installation, copy the 'User OAuth Token'")
    print("   - It starts with 'xoxp-'")
    print("   - Add it to your .env file as SLACK_USER_TOKEN")
    
    print("\n4️⃣  TEST YOUR SETUP:")
    print("   - Run: python test_autonomous_access.py")
    print("   - You should see access to many channels")

def main():
    """Main setup function."""
    print("🤖 Autonomous Slack Bot Setup")
    print("=" * 40)
    
    # Check current state
    check_env_file()
    test_current_tokens()
    
    # Ask user what they want to do
    print("What would you like to do?")
    print("1. Generate .env template file")
    print("2. Show detailed setup instructions")
    print("3. Test current configuration")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        generate_env_template()
        print("\n✅ Template created! Edit .env with your tokens, then run:")
        print("   python test_autonomous_access.py")
        
    elif choice == "2":
        show_setup_instructions()
        
    elif choice == "3":
        print("\n🔍 Running comprehensive test...")
        os.system("python test_autonomous_access.py")
        
    elif choice == "4":
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 