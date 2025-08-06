#!/usr/bin/env python
"""
Admin script to add a bot to all private channels.
This script should be run by a workspace admin who has access to all private channels.
"""
import os
from pathlib import Path
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

# Load environment
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

def add_bot_to_all_private_channels():
    """Add bot to all private channels (admin only)."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not found in .env file")
        print("   Please add your bot token to the .env file")
        return
    
    client = WebClient(token=token)
    
    try:
        # Test authentication
        auth_resp = client.auth_test()
        bot_user_id = auth_resp['user_id']
        print(f"✅ Bot authenticated: {auth_resp['user']} (ID: {bot_user_id})")
        
        # Get all private channels
        print("🔍 Getting all private channels...")
        resp = client.conversations_list(types="private_channel", limit=1000)
        private_channels = resp["channels"]
        
        print(f"🔒 Found {len(private_channels)} private channels")
        
        # Add bot to each private channel
        added_count = 0
        already_member_count = 0
        failed_count = 0
        no_permission_count = 0
        
        for i, channel in enumerate(private_channels, 1):
            channel_name = channel.get("name", "unknown")
            channel_id = channel["id"]
            
            print(f"[{i}/{len(private_channels)}] Processing #{channel_name}...")
            
            if channel.get("is_member", False):
                print(f"   ✅ Bot already a member of #{channel_name}")
                already_member_count += 1
                continue
            
            try:
                # Try to invite bot to private channel
                client.conversations_invite(
                    channel=channel_id,
                    users=bot_user_id
                )
                print(f"   ✅ Added bot to #{channel_name}")
                added_count += 1
                
            except SlackApiError as e:
                if e.response.status_code == 403:
                    print(f"   ❌ No permission to invite to #{channel_name} (not admin)")
                    no_permission_count += 1
                elif e.response.status_code == 429:
                    print(f"   ⏳ Rate limited, waiting...")
                    import time
                    time.sleep(60)  # Wait 1 minute
                    try:
                        client.conversations_invite(
                            channel=channel_id,
                            users=bot_user_id
                        )
                        print(f"   ✅ Added bot to #{channel_name} (after retry)")
                        added_count += 1
                    except:
                        print(f"   ❌ Failed to add bot to #{channel_name} after retry")
                        failed_count += 1
                else:
                    print(f"   ❌ Failed to add bot to #{channel_name}: {e}")
                    failed_count += 1
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total private channels: {len(private_channels)}")
        print(f"   Already member: {already_member_count}")
        print(f"   Successfully added: {added_count}")
        print(f"   No permission: {no_permission_count}")
        print(f"   Failed to add: {failed_count}")
        
        if added_count > 0:
            print(f"\n🎉 Success! Bot now has access to {added_count} additional private channels")
        else:
            print(f"\n⚠️  No new channels were added. Check permissions.")
        
    except SlackApiError as e:
        print(f"❌ Error: {e}")

def show_admin_instructions():
    """Show instructions for admin setup."""
    print("🔧 ADMIN SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("\n🎯 GOAL: Add bot to all private channels")
    print("   This requires workspace admin privileges")
    
    print("\n1️⃣  ENSURE BOT HAS ADMIN PRIVILEGES:")
    print("   - Go to https://api.slack.com/apps")
    print("   - Select your bot app")
    print("   - Go to 'OAuth & Permissions'")
    print("   - Ensure bot has these scopes:")
    print("     • channels:read")
    print("     • groups:read")
    print("     • channels:history")
    print("     • users:read")
    print("     • groups:write (for private channel access)")
    
    print("\n2️⃣  INSTALL WITH ADMIN PRIVILEGES:")
    print("   - Click 'Install to Workspace'")
    print("   - Grant admin privileges during installation")
    print("   - This allows the bot to be added to private channels")
    
    print("\n3️⃣  RUN THIS SCRIPT:")
    print("   - Ensure SLACK_BOT_TOKEN is in .env file")
    print("   - Run: python add_bot_to_private_channels.py")
    print("   - This will add the bot to all private channels")
    
    print("\n4️⃣  VERIFY ACCESS:")
    print("   - Run: python test_channels.py")
    print("   - Should show access to many private channels")

def main():
    """Main function."""
    print("🔧 ADD BOT TO PRIVATE CHANNELS")
    print("=" * 40)
    
    print("This script adds your bot to all private channels.")
    print("⚠️  Requires workspace admin privileges!")
    
    print("\nWhat would you like to do?")
    print("1. Show admin setup instructions")
    print("2. Add bot to all private channels")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        show_admin_instructions()
        
    elif choice == "2":
        print("\n🔍 Running bot addition script...")
        add_bot_to_all_private_channels()
        
    elif choice == "3":
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 