#!/usr/bin/env python
"""
Slack API client and data fetching functionality.
"""
import time
from datetime import datetime
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from config.config_manager import get_required_env_vars, PipelineConfig


class SlackDataFetcher:
    """Handles all Slack API interactions and data fetching."""
    
    def __init__(self):
        env_vars = get_required_env_vars()
        self.client = WebClient(token=env_vars['SLACK_TOKEN'])
        self.config = PipelineConfig()
        self.token_type = env_vars.get('TOKEN_TYPE', 'BOT_TOKEN')
        print(f"🔑 Using {self.token_type} for Slack access")
        
    def get_all_accessible_channels(self):
        """Get all channels the bot/user can access based on token type."""
        channels = []
        
        if self.token_type == 'USER_TOKEN':
            # User token can access all public channels and private channels the user is in
            print("🔍 User token detected - scanning all accessible channels...")
            
            # Get public channels
            try:
                resp = self.client.conversations_list(types="public_channel", limit=1000)
                public_channels = [ch["id"] for ch in resp["channels"]]
                channels.extend(public_channels)
                print(f"Found {len(public_channels)} public channels")
            except SlackApiError as e:
                print(f"Failed to get public channels: {e}")
            
            # Get private channels the user is in
            try:
                resp = self.client.conversations_list(types="private_channel", limit=1000)
                private_channels = [ch["id"] for ch in resp["channels"]]
                channels.extend(private_channels)
                print(f"Found {len(private_channels)} private channels (user is member)")
            except SlackApiError as e:
                print(f"Failed to get private channels: {e}")
                
        else:
            # Bot token - only channels bot is member of
            print("🔍 Bot token detected - scanning member channels only...")
            channels = self.get_member_channels()
            
        return channels
    
    def get_member_channels(self):
        """Get channels bot is member of (for bot tokens)."""
        channels = []
        try:
            resp = self.client.conversations_list(types="private_channel", limit=1000)
            member_channels = [ch["id"] for ch in resp["channels"] if ch.get("is_member", False)]
            channels.extend(member_channels)
            print(f"Found {len(member_channels)} private channels (bot is member)")
        except SlackApiError as e:
            print(f"Failed to get channels: {e}")
        return channels
    
    def get_user_name(self, user_id):
        """Get user display name for context."""
        try:
            resp = self.client.users_info(user=user_id)
            time.sleep(self.config.SLACK_USERS_BATCH_DELAY)  # Rate limit for users_info
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
                # Only add delay after API calls, not for cached/failed lookups
                if i > 0 and i % 10 == 0:  # Progress indicator every 10 users
                    print(f"   Progress: {i}/{len(user_ids)} users processed")
        
        print(f"   ✅ Processed {len(user_names)} user names")
        return user_names