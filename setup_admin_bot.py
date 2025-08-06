#!/usr/bin/env python
"""
Setup script for creating a Slack bot with admin privileges for autonomous access.
This helps overcome personal permission limitations.
"""
import os
from pathlib import Path
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

def show_admin_bot_setup():
    """Show instructions for creating an admin bot."""
    print("🔧 ADMIN BOT SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("\n🎯 GOAL: Create a bot with workspace admin privileges")
    print("   This allows the bot to access all channels regardless of your personal permissions")
    
    print("\n1️⃣  CREATE A NEW SLACK APP:")
    print("   - Go to https://api.slack.com/apps")
    print("   - Click 'Create New App'")
    print("   - Choose 'From scratch'")
    print("   - Name it something like 'QA Bot Admin'")
    print("   - Select your workspace")
    
    print("\n2️⃣  CONFIGURE BOT PERMISSIONS:")
    print("   - Go to 'OAuth & Permissions'")
    print("   - Under 'Scopes', add these BOT TOKEN SCOPES:")
    print("     • channels:read")
    print("     • groups:read")
    print("     • channels:history")
    print("     • users:read")
    print("     • channels:join (to join public channels)")
    print("     • groups:write (to access private channels)")
    
    print("\n3️⃣  INSTALL WITH ADMIN PRIVILEGES:")
    print("   - Click 'Install to Workspace'")
    print("   - IMPORTANT: During installation, grant admin privileges")
    print("   - This allows the bot to access all channels")
    
    print("\n4️⃣  GET THE BOT TOKEN:")
    print("   - Copy the 'Bot User OAuth Token' (starts with 'xoxb-')")
    print("   - Add it to your .env file as SLACK_BOT_TOKEN")
    
    print("\n5️⃣  AUTO-JOIN ALL PUBLIC CHANNELS:")
    print("   - Run the auto-join script below")
    print("   - This gives the bot access to all public channels")

def create_auto_join_script():
    """Create a script to auto-join all public channels."""
    script_content = '''#!/usr/bin/env python
"""
Auto-join script for admin bot to access all public channels.
Run this once to give your bot access to all public channels.
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

def auto_join_public_channels():
    """Join all public channels with admin bot."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not found in .env file")
        return
    
    client = WebClient(token=token)
    
    try:
        # Test authentication
        auth_resp = client.auth_test()
        print(f"✅ Bot authenticated: {auth_resp['user']}")
        
        # Get all public channels
        print("🔍 Getting all public channels...")
        resp = client.conversations_list(types="public_channel", limit=1000)
        channels = resp["channels"]
        
        print(f"📢 Found {len(channels)} public channels")
        
        # Join each channel
        joined_count = 0
        already_member_count = 0
        failed_count = 0
        
        for i, channel in enumerate(channels, 1):
            channel_name = channel.get("name", "unknown")
            channel_id = channel["id"]
            
            print(f"[{i}/{len(channels)}] Processing #{channel_name}...")
            
            if channel.get("is_member", False):
                print(f"   ✅ Already a member of #{channel_name}")
                already_member_count += 1
                continue
            
            try:
                client.conversations_join(channel=channel_id)
                print(f"   ✅ Joined #{channel_name}")
                joined_count += 1
            except SlackApiError as e:
                if e.response.status_code == 429:
                    print(f"   ⏳ Rate limited, waiting...")
                    import time
                    time.sleep(60)  # Wait 1 minute
                    try:
                        client.conversations_join(channel=channel_id)
                        print(f"   ✅ Joined #{channel_name} (after retry)")
                        joined_count += 1
                    except:
                        print(f"   ❌ Failed to join #{channel_name} after retry")
                        failed_count += 1
                else:
                    print(f"   ❌ Failed to join #{channel_name}: {e}")
                    failed_count += 1
        
        print(f"\\n📊 SUMMARY:")
        print(f"   Total channels: {len(channels)}")
        print(f"   Already member: {already_member_count}")
        print(f"   Successfully joined: {joined_count}")
        print(f"   Failed to join: {failed_count}")
        
        if failed_count == 0:
            print(f"\\n🎉 Success! Bot now has access to all public channels")
        else:
            print(f"\\n⚠️  Some channels failed to join. This is normal for restricted channels.")
        
    except SlackApiError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    auto_join_public_channels()
'''
    
    with open("auto_join_channels.py", "w") as f:
        f.write(script_content)
    
    print("✅ Created auto_join_channels.py")
    print("   Run this script to give your bot access to all public channels")

def create_enhanced_bot_client():
    """Create an enhanced bot client that can access more channels."""
    enhanced_client_content = '''#!/usr/bin/env python
"""
Enhanced Slack client with admin privileges for broader channel access.
"""
import time
from datetime import datetime
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from config_manager import get_required_env_vars, PipelineConfig

class AdminSlackDataFetcher:
    """Enhanced Slack client with admin privileges for autonomous access."""
    
    def __init__(self):
        env_vars = get_required_env_vars()
        self.client = WebClient(token=env_vars['SLACK_TOKEN'])
        self.config = PipelineConfig()
        self.token_type = env_vars.get('TOKEN_TYPE', 'BOT_TOKEN')
        print(f"🔑 Using {self.token_type} with admin privileges")
        
    def get_all_channels_with_admin_access(self):
        """Get all channels with admin bot access."""
        channels = []
        
        # Get all public channels (admin bot can access all)
        try:
            resp = self.client.conversations_list(types="public_channel", limit=1000)
            public_channels = [ch["id"] for ch in resp["channels"]]
            channels.extend(public_channels)
            print(f"Found {len(public_channels)} public channels (admin access)")
        except SlackApiError as e:
            print(f"Failed to get public channels: {e}")
        
        # Get private channels where bot is member
        try:
            resp = self.client.conversations_list(types="private_channel", limit=1000)
            private_channels = [ch["id"] for ch in resp["channels"] if ch.get("is_member", False)]
            channels.extend(private_channels)
            print(f"Found {len(private_channels)} private channels (bot is member)")
        except SlackApiError as e:
            print(f"Failed to get private channels: {e}")
        
        return channels
    
    def join_public_channel(self, channel_id):
        """Join a public channel with admin privileges."""
        try:
            self.client.conversations_join(channel=channel_id)
            return True
        except SlackApiError as e:
            print(f"Failed to join channel {channel_id}: {e}")
            return False
    
    def get_user_name(self, user_id):
        """Get user display name for context."""
        try:
            resp = self.client.users_info(user=user_id)
            time.sleep(self.config.SLACK_USERS_BATCH_DELAY)
            return resp["user"]["real_name"] or resp["user"]["name"]
        except:
            return f"User{user_id[-4:]}"
    
    def fetch_recent_messages(self, channel_id, max_messages=None):
        """Fetch recent messages from channel (rate-limit friendly)."""
        if max_messages is None:
            max_messages = self.config.MAX_MESSAGES_PER_CHANNEL
            
        all_messages = []
        cursor = None
        fetched = 0
        
        print(f"📥 Fetching up to {max_messages} recent messages from {channel_id}...")
        
        while fetched < max_messages:
            try:
                batch_size = min(self.config.SLACK_API_BATCH_SIZE, max_messages - fetched)
                resp = self.client.conversations_history(
                    channel=channel_id,
                    limit=batch_size,
                    cursor=cursor
                )
                messages = resp["messages"]
                if not messages:
                    break
                    
                all_messages.extend(reversed(messages))
                fetched += len(messages)
                
                response_metadata = resp.get("response_metadata")
                cursor = response_metadata.get("next_cursor") if response_metadata else None
                
                if not cursor:
                    break
                    
                time.sleep(self.config.SLACK_API_DELAY)
                
            except SlackApiError as e:
                if e.response.status_code == 429:
                    wait_time = int(e.response.headers.get("Retry-After", self.config.RATE_LIMIT_RETRY_DELAY))
                    print(f"⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time + 1)
                    continue
                else:
                    print(f"❌ Slack API error: {e}")
                    break
        
        print(f"   ✅ Fetched {len(all_messages)} messages")
        return all_messages
    
    def get_user_names_for_messages(self, messages):
        """Get user names for all users in message list - BATCHED for performance."""
        user_ids = set(msg.get("user") for msg in messages if msg.get("user"))
        user_names = {}
        
        print(f"🔍 Looking up {len(user_ids)} unique users...")
        
        for i, user_id in enumerate(user_ids):
            if user_id:
                user_names[user_id] = self.get_user_name(user_id)
                if i > 0 and i % 10 == 0:
                    print(f"   Progress: {i}/{len(user_ids)} users processed")
        
        print(f"   ✅ Processed {len(user_names)} user names")
        return user_names
'''
    
    with open("admin_slack_client.py", "w") as f:
        f.write(enhanced_client_content)
    
    print("✅ Created admin_slack_client.py")
    print("   This enhanced client has admin privileges for broader access")

def main():
    """Main setup function."""
    print("🔧 ADMIN BOT SETUP")
    print("=" * 30)
    
    print("This setup helps create a bot with admin privileges")
    print("to overcome personal permission limitations.")
    
    print("\nWhat would you like to do?")
    print("1. Show admin bot setup instructions")
    print("2. Create auto-join script for public channels")
    print("3. Create enhanced admin client")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        show_admin_bot_setup()
        
    elif choice == "2":
        create_auto_join_script()
        print("\n📝 Next steps:")
        print("   1. Follow the admin bot setup instructions")
        print("   2. Run: python auto_join_channels.py")
        print("   3. Your bot will have access to all public channels")
        
    elif choice == "3":
        create_enhanced_bot_client()
        print("\n📝 Next steps:")
        print("   1. Use admin_slack_client.py instead of slack_client.py")
        print("   2. Update your imports to use AdminSlackDataFetcher")
        print("   3. The admin client has broader access capabilities")
        
    elif choice == "4":
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 