# Autonomous Slack Bot Access Guide

This guide explains how to give your Slack bot autonomous access to channels without manual invitations.

## 🎯 Overview

Your Slack bot can now access channels autonomously using **User Tokens** instead of requiring manual invitations to each channel.

## 🔑 Token Types Comparison

| Feature | Bot Token | User Token |
|---------|-----------|------------|
| **Channel Access** | Only invited channels | All public + user's private channels |
| **Setup Required** | Manual invitations | None (autonomous) |
| **Permissions** | Limited bot permissions | Full user permissions |
| **Best For** | Specific bot functionality | Data collection/analysis |

## 🚀 Setup Instructions

### Option 1: User Token (Recommended for Autonomous Access)

1. **Create a User Token:**
   - Go to https://api.slack.com/apps
   - Select your app or create a new one
   - Go to "OAuth & Permissions"
   - Under "Scopes", add these permissions:
     - `channels:read` - Read public channels
     - `groups:read` - Read private channels
     - `channels:history` - Read channel messages
     - `users:read` - Read user information
   - Click "Install to Workspace"
   - Copy the "User OAuth Token" (starts with `xoxp-`)

2. **Update your `.env` file:**
   ```bash
   SLACK_USER_TOKEN=xoxp-your-user-token-here
   OPENAI_API_KEY=your-openai-key
   ```

3. **Test autonomous access:**
   ```bash
   python test_autonomous_access.py
   ```

### Option 2: Enhanced Bot Token (Limited Autonomous)

If you prefer to stick with bot tokens but want broader access:

1. **Add bot to public channels automatically:**
   ```bash
   # Add bot to all public channels (run once)
   python -c "
   from slack_sdk.web import WebClient
   client = WebClient(token='your-bot-token')
   channels = client.conversations_list(types='public_channel')['channels']
   for channel in channels:
       try:
           client.conversations_join(channel=channel['id'])
           print(f'Joined {channel[\"name\"]}')
       except:
           print(f'Could not join {channel[\"name\"]}')
   "
   ```

2. **Use the existing bot token setup:**
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-bot-token-here
   ```

## 🔍 Testing Your Setup

### Test Autonomous Access
```bash
python test_autonomous_access.py
```

This will show you:
- How many channels each token type can access
- Authentication status
- Channel access comparison

### Test Channel Processing
```bash
python test_channels.py
```

This shows detailed channel access information.

## 📊 Expected Results

### With User Token:
- ✅ Access to ALL public channels automatically
- ✅ Access to private channels where the user is a member
- ✅ No manual invitations required
- ✅ Can process hundreds of channels autonomously

### With Bot Token:
- ❌ Only channels where bot was manually invited
- ❌ Requires manual setup for each channel
- ❌ Limited to specific channels only

## 🛡️ Security Considerations

### User Token Security:
- **Scope**: User tokens have the same permissions as the user who created them
- **Access**: Can read all messages in accessible channels
- **Recommendation**: Use a dedicated service account user, not your personal account

### Bot Token Security:
- **Scope**: Limited to bot-specific permissions
- **Access**: Only channels where bot is explicitly added
- **Recommendation**: More restrictive, good for production bots

## 🔧 Configuration

Your bot now automatically detects the token type and adjusts behavior:

```python
# In slack_client.py
if self.token_type == 'USER_TOKEN':
    # Autonomous access to all public channels
    channels = self.get_all_public_channels()
else:
    # Bot token - only member channels
    channels = self.get_member_channels()
```

## 🚀 Running with Autonomous Access

Once configured with a user token:

```bash
# Run the complete pipeline with autonomous access
python run_pipeline.py

# Or run individual components
python qa_extractor.py
```

## 📈 Performance Benefits

- **No Manual Setup**: Automatically processes all accessible channels
- **Scalable**: Can handle hundreds of channels without configuration
- **Efficient**: Processes channels in parallel where possible
- **Flexible**: Can easily add/remove channels by managing user membership

## 🐛 Troubleshooting

### Common Issues:

1. **"Missing required environment variables"**
   - Ensure either `SLACK_USER_TOKEN` or `SLACK_BOT_TOKEN` is set in `.env`

2. **"Authentication failed"**
   - Check token validity and permissions
   - Ensure app is installed to workspace

3. **"No channels accessible"**
   - User token: Ensure user has access to channels
   - Bot token: Invite bot to desired channels

4. **Rate limiting**
   - The bot includes automatic rate limit handling
   - Adjust delays in `config_manager.py` if needed

### Getting Help:
```bash
# Test token access
python test_autonomous_access.py

# Check channel access
python test_channels.py

# Run with verbose logging
python run_pipeline.py
```

## 🎉 Success!

With autonomous access configured, your bot can now:
- Process all public channels automatically
- Access private channels where the user is a member
- Scale to handle large workspaces
- Run without manual channel management

The bot will automatically detect and process all accessible channels, making it truly autonomous! 