# 🚀 Slack QA Bot Deployment Guide

Complete step-by-step guide to deploy your QA bot to production.

## 📋 Prerequisites

- ✅ Slack workspace (admin access required)
- ✅ OpenAI API account
- ✅ GitHub account
- ✅ Render.com account (free tier works)

---

## 🔧 Step 1: Create Slack App

### 1.1 Go to Slack API Portal
1. Visit https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter:
   - **App Name**: `QA Bot` (or your preferred name)
   - **Workspace**: Select your workspace
5. Click **"Create App"**

### 1.2 Configure Bot User
1. In your app dashboard, go to **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   ```
   channels:history
   channels:read
   chat:write
   groups:history
   groups:read
   im:history
   im:read
   mpim:history
   mpim:read
   users:read
   ```
4. Click **"Install to Workspace"**
5. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### 1.3 Enable Socket Mode
1. Go to **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to ON
3. Create a new App-Level Token:
   - **Token Name**: `socket-token`
   - **Scopes**: `connections:write`
4. Copy the **App-Level Token** (starts with `xapp-`)

### 1.4 Subscribe to Events
1. Go to **"Event Subscriptions"**
2. Toggle **"Enable Events"** to ON
3. Under **"Subscribe to bot events"**, add:
   ```
   message.channels
   message.groups
   message.im
   message.mpim
   ```
4. Click **"Save Changes"**

---

## 🔑 Step 2: Get OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Name it `qa-bot-key`
4. Copy the key (starts with `sk-`)
5. **Important**: Add credits to your OpenAI account (~$5-10 is plenty)

---

## ⚙️ Step 3: Configure Environment Variables

### 3.1 Update Local .env File
```bash
# Add your actual keys to .env file
cat > .env << 'EOF'
# Slack Tokens
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-level-token-here

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Custom settings
OPENAI_MODEL=gpt-4o-mini
QUESTION_DETECTION_THRESHOLD=0.7
ANSWER_DETECTION_THRESHOLD=0.6
EOF
```

### 3.2 Replace Placeholder Values
**Replace these in your .env file:**
- `xoxb-your-bot-token-here` → Your Bot Token from Step 1.2
- `xapp-your-app-level-token-here` → Your App Token from Step 1.3  
- `sk-your-openai-api-key-here` → Your OpenAI key from Step 2

---

## 🧪 Step 4: Test Local Deployment

### 4.1 Install Dependencies
```bash
cd qa-slackbot
source ../myenv/bin/activate
pip install -r requirements.txt
```

### 4.2 Test Configuration
```bash
# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Test environment setup
python3 -c "
import os
print('✅ SLACK_BOT_TOKEN:', 'Present' if os.getenv('SLACK_BOT_TOKEN') else '❌ Missing')
print('✅ SLACK_APP_TOKEN:', 'Present' if os.getenv('SLACK_APP_TOKEN') else '❌ Missing') 
print('✅ OPENAI_API_KEY:', 'Present' if os.getenv('OPENAI_API_KEY') else '❌ Missing')
"
```

### 4.3 Run Local Test
```bash
# Start the bot locally
python3 start.py
```

**Expected Output:**
```
🚀 Starting Slack Q&A Bot on Render...
✅ All required environment variables found
📁 No DATABASE_URL found, will use SQLite fallback
🔄 Initializing real-time Q&A monitor...
🎯 Starting real-time monitoring (press Ctrl+C to stop)...
```

### 4.4 Test in Slack
1. Go to your Slack workspace
2. Find the QA Bot in **Apps** section
3. Test with a message like: `"How do I deploy this app?"`
4. Wait ~30 seconds, then respond: `"You can use Render or Heroku"`
5. Check if the bot processes the conversation

### 4.5 Stop Local Test
Press `Ctrl+C` to stop the local bot.

---

## 🌐 Step 5: Deploy to Render.com

### 5.1 Prepare Repository
```bash
# Initialize git repo (if not already)
git init
git add .
git commit -m "Initial commit - QA Bot ready for deployment"

# Push to GitHub
# Create new repo at github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/qa-slackbot.git
git branch -M main
git push -u origin main
```

### 5.2 Create Render Account
1. Go to https://render.com
2. Sign up using GitHub (recommended)
3. Authorize Render to access your repositories

### 5.3 Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `qa-slackbot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start.py`
   - **Instance Type**: `Free` (upgrade later if needed)

### 5.4 Add Environment Variables
In Render dashboard → **Environment**:

```bash
SLACK_BOT_TOKEN=xoxb-your-actual-token
SLACK_APP_TOKEN=xapp-your-actual-token  
OPENAI_API_KEY=sk-your-actual-key
OPENAI_MODEL=gpt-4o-mini
QUESTION_DETECTION_THRESHOLD=0.7
ANSWER_DETECTION_THRESHOLD=0.6
```

### 5.5 Create PostgreSQL Database (Optional)
1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `qa-slackbot-db`
   - **Database**: `qa_bot`
   - **User**: `qa_bot_user`
   - **Region**: Same as your web service
3. After creation, copy the **External Database URL**
4. Add to your web service environment variables:
   ```
   DATABASE_URL=your-postgresql-connection-string
   ```

### 5.6 Deploy
1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Monitor the **Logs** tab for any errors

---

## ✅ Step 6: Verify Production Deployment

### 6.1 Check Deployment Status
**In Render Logs, you should see:**
```
🚀 Starting Slack Q&A Bot on Render...
✅ All required environment variables found
🐘 Using PostgreSQL database: postgresql://...
🎯 Starting real-time monitoring...
```

### 6.2 Test Production Bot
1. Go to your Slack workspace
2. Post a question in any channel the bot has access to
3. Post an answer from someone else
4. Wait ~1 minute for processing

### 6.3 View Web Dashboard (Optional)
```bash
# Add web viewer to your bot (if not already done)
# Create separate web service or add to existing:
# Start Command: python web_viewer.py
```

### 6.4 Export Data Test
```bash
# SSH into Render service (if needed) or test locally:
python3 -c "
from database.database_manager import DatabaseManager
db = DatabaseManager()
stats = db.get_statistics()
print(f'✅ Database contains {stats[\"qa_pairs\"]} Q&A pairs')
db.export_to_csv('production_qa_export.csv')
print('✅ Export successful')
"
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Bot not responding in Slack**
```bash
# Check Render logs for errors
# Verify tokens are correct
# Ensure bot is invited to channels
```

**2. OpenAI API errors**
```bash
# Check API key is valid
# Verify account has credits
# Check rate limits
```

**3. Database connection issues**
```bash
# For SQLite: Check file permissions
# For PostgreSQL: Verify DATABASE_URL
# Check Render service connectivity
```

### Debug Commands
```bash
# Test individual components
python3 test_manual.py

# Check configuration
python3 -c "from config.config_manager import get_required_env_vars; print(get_required_env_vars())"

# Test database
python3 -c "from database.database_manager import DatabaseManager; print(DatabaseManager().get_statistics())"
```

---

## 💰 Cost Estimates

### Free Tier (First Month)
- **Render Web Service**: 750 hours free
- **PostgreSQL**: Free tier included  
- **OpenAI**: ~$1-5/month for small team
- **Total**: ~$1-5/month

### Production (After Free Tier)
- **Render**: ~$7/month
- **PostgreSQL**: ~$7/month (if using external)
- **OpenAI**: ~$5-20/month depending on usage
- **Total**: ~$19-34/month

---

## 🎯 Next Steps

1. **Monitor Performance**: Check Render logs daily for first week
2. **Adjust Thresholds**: Fine-tune confidence scores based on results
3. **Add Channels**: Invite bot to more Slack channels
4. **Export Data**: Regular exports for analysis
5. **Scale Up**: Upgrade Render instance if needed

---

## 🆘 Support

- **Slack API Docs**: https://api.slack.com/web
- **OpenAI Docs**: https://platform.openai.com/docs
- **Render Docs**: https://render.com/docs
- **GitHub Issues**: Create issues in your repo for tracking

---

**Ready to deploy? Start with Step 1! 🚀**