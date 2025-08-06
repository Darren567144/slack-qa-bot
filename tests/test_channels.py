#!/usr/bin/env python
"""
Test script to check what channels the Slack bot can access.
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
                # Remove quotes if present
                value = value.strip('"').strip("'")
                os.environ[key] = value

TOKEN = os.environ.get("SLACK_BOT_TOKEN")
if not TOKEN:
    print("❌ SLACK_BOT_TOKEN environment variable not set!")
    exit(1)

client = WebClient(token=TOKEN)

print("🔍 Testing Slack bot channel access...\n")

def test_auth():
    """Test if the bot token is valid."""
    try:
        resp = client.auth_test()
        print(f"✅ Bot authenticated successfully!")
        print(f"   Bot User ID: {resp['user_id']}")
        print(f"   Bot User: {resp['user']}")
        print(f"   Team: {resp['team']}")
        return True
    except SlackApiError as e:
        print(f"❌ Authentication failed: {e}")
        return False

def get_public_channels():
    """Get all public channels."""
    try:
        resp = client.conversations_list(types="public_channel", limit=1000)
        channels = resp["channels"]
        print(f"\n📢 PUBLIC CHANNELS ({len(channels)} total):")
        for ch in channels[:10]:  # Show first 10
            member_status = "✅ Member" if ch.get("is_member", False) else "❌ Not member"
            print(f"   {ch['name']} ({ch['id']}) - {member_status}")
        if len(channels) > 10:
            print(f"   ... and {len(channels) - 10} more")
        return [ch["id"] for ch in channels if ch.get("is_member", False)]
    except SlackApiError as e:
        print(f"❌ Failed to get public channels: {e}")
        return []

def get_private_channels():
    """Get private channels bot is member of."""
    try:
        resp = client.conversations_list(types="private_channel", limit=1000)
        channels = resp["channels"]
        member_channels = [ch for ch in channels if ch.get("is_member", False)]
        print(f"\n🔒 PRIVATE CHANNELS (member of {len(member_channels)} out of {len(channels)} total):")
        for ch in member_channels:
            print(f"   {ch['name']} ({ch['id']}) - ✅ Member")
        if len(channels) - len(member_channels) > 0:
            print(f"   Note: Bot is NOT a member of {len(channels) - len(member_channels)} other private channels")
        return [ch["id"] for ch in member_channels]
    except SlackApiError as e:
        print(f"❌ Failed to get private channels: {e}")
        return []

def test_sample_messages(channel_id):
    """Test fetching a few messages from a channel."""
    try:
        resp = client.conversations_history(channel=channel_id, limit=5)
        messages = resp["messages"]
        print(f"\n💬 Sample from channel {channel_id} ({len(messages)} recent messages):")
        for msg in messages[:3]:
            text = msg.get("text", "")[:100] + ("..." if len(msg.get("text", "")) > 100 else "")
            user = msg.get("user", "unknown")
            print(f"   [{user}]: {text}")
        return True
    except SlackApiError as e:
        print(f"❌ Failed to fetch messages from {channel_id}: {e}")
        return False

def main():
    # Test authentication
    if not test_auth():
        return
    
    # Get accessible channels
    public_channels = get_public_channels()
    private_channels = get_private_channels()
    
    all_accessible = public_channels + private_channels
    print(f"\n📊 SUMMARY:")
    print(f"   Total accessible channels: {len(all_accessible)}")
    print(f"   Public channels (member): {len(public_channels)}")
    print(f"   Private channels (member): {len(private_channels)}")
    
    if all_accessible:
        print(f"\n✅ Bot can access these channel IDs:")
        print(f"   {','.join(all_accessible)}")
        
        # Test fetching messages from first accessible channel
        print(f"\n🧪 Testing message access...")
        test_sample_messages(all_accessible[0])
    else:
        print(f"\n❌ Bot has no accessible channels!")
        print(f"   Make sure to:")
        print(f"   1. Add bot to public channels you want to monitor")
        print(f"   2. Invite bot to private channels with: /invite @YourBotName")

if __name__ == "__main__":
    main()