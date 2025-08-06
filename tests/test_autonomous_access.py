#!/usr/bin/env python
"""
Test script to demonstrate autonomous Slack access capabilities.
This shows the difference between bot tokens and user tokens for channel access.
"""
import os
from pathlib import Path
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

# Try to load .env file if it exists
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                value = value.strip('"').strip("'")
                os.environ[key] = value

def test_token_access(token, token_type):
    """Test what channels a token can access."""
    client = WebClient(token=token)
    
    print(f"\n🔑 Testing {token_type} access...")
    
    # Test authentication
    try:
        auth_resp = client.auth_test()
        print(f"✅ {token_type} authenticated successfully!")
        print(f"   User ID: {auth_resp['user_id']}")
        print(f"   User: {auth_resp['user']}")
        print(f"   Team: {auth_resp['team']}")
    except SlackApiError as e:
        print(f"❌ {token_type} authentication failed: {e}")
        return
    
    # Test public channel access
    try:
        resp = client.conversations_list(types="public_channel", limit=1000)
        public_channels = resp["channels"]
        accessible_public = [ch for ch in public_channels if ch.get("is_member", False)]
        print(f"📢 Public channels: {len(accessible_public)} accessible out of {len(public_channels)} total")
    except SlackApiError as e:
        print(f"❌ Failed to get public channels: {e}")
    
    # Test private channel access
    try:
        resp = client.conversations_list(types="private_channel", limit=1000)
        private_channels = resp["channels"]
        accessible_private = [ch for ch in private_channels if ch.get("is_member", False)]
        print(f"🔒 Private channels: {len(accessible_private)} accessible out of {len(private_channels)} total")
    except SlackApiError as e:
        print(f"❌ Failed to get private channels: {e}")
    
    return len(accessible_public) + len(accessible_private)

def main():
    print("🚀 Testing Autonomous Slack Access\n")
    
    # Test bot token if available
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    if bot_token:
        bot_access = test_token_access(bot_token, "BOT_TOKEN")
    else:
        print("❌ SLACK_BOT_TOKEN not found")
        bot_access = 0
    
    # Test user token if available
    user_token = os.environ.get("SLACK_USER_TOKEN")
    if user_token:
        user_access = test_token_access(user_token, "USER_TOKEN")
    else:
        print("❌ SLACK_USER_TOKEN not found")
        user_access = 0
    
    # Summary
    print(f"\n📊 ACCESS SUMMARY:")
    print(f"   Bot token channels: {bot_access}")
    print(f"   User token channels: {user_access}")
    
    if user_access > bot_access:
        print(f"\n✅ User token provides {user_access - bot_access} more channels!")
        print(f"   This gives autonomous access without manual invitations.")
    elif bot_access > 0:
        print(f"\n⚠️  Bot token has limited access ({bot_access} channels)")
        print(f"   Consider using a user token for broader access.")
    else:
        print(f"\n❌ No tokens configured!")
        print(f"   Set either SLACK_BOT_TOKEN or SLACK_USER_TOKEN in your .env file")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. Use SLACK_USER_TOKEN for autonomous access to all public channels")
    print(f"   2. User tokens can access private channels the user is already in")
    print(f"   3. No need to invite bots to channels manually")
    print(f"   4. User tokens have the same permissions as the user who created them")

if __name__ == "__main__":
    main() 