# 🚀 Cloud Deployment Guide for Slack Q&A Bot

This guide shows how to deploy your Slack bot with a cloud PostgreSQL database for production use.

## 🎯 Recommended Setup: Neon + Railway

**Why this combo:**
- ✅ Both have generous free tiers
- ✅ PostgreSQL database accessible from anywhere  
- ✅ Easy deployment for the bot application
- ✅ Scales with your team size

## 📊 Step 1: Set Up Neon Database (2 minutes)

### 1. Create Free Neon Account
1. Go to https://neon.tech
2. Sign up with GitHub/Google (no credit card needed)
3. Create a new project: "slack-qa-bot"

### 2. Get Database URL
1. Go to your project dashboard
2. Click "Connection Details"
3. Copy the connection string (looks like):
   ```
   postgresql://username:password@hostname/dbname?sslmode=require
   ```

### 3. Test Connection (Optional)
```bash
# Install psql client
brew install postgresql  # macOS
sudo apt-get install postgresql-client  # Linux

# Test connection
psql "postgresql://your-connection-string-here"
```

## 🤖 Step 2: Update Your Bot Code

### 1. Install New Dependencies
```bash
pip install -r requirements.txt
```

The updated `requirements.txt` now includes:
- `psycopg2-binary` for PostgreSQL
- `sqlalchemy` for database ORM

### 2. Update Environment Variables
Create/update your `.env` file:
```bash
# Slack credentials  
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-level-token
OPENAI_API_KEY=sk-your-openai-key

# NEW: Database URL (replace with your Neon URL)
DATABASE_URL=postgresql://username:password@hostname/dbname?sslmode=require
```

### 3. Update Imports
Replace the old database manager:
```python
# OLD
from database_manager import DatabaseManager

# NEW  
from cloud_database_manager import CloudDatabaseManager as DatabaseManager
```

That's it! The new `CloudDatabaseManager` automatically detects PostgreSQL and creates all tables.

## 🌐 Step 3: Deploy Bot Application

### Option A: Railway (Easiest)
1. Go to https://railway.app
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy automatically updates when you push code

### Option B: Render
1. Go to https://render.com  
2. Connect GitHub repository
3. Choose "Web Service"
4. Add environment variables
5. Deploy

### Option C: Heroku
1. Install Heroku CLI
2. `heroku create your-slack-bot`
3. `heroku config:set DATABASE_URL=your-neon-url`
4. `git push heroku main`

## 🔧 Step 4: Slack App Configuration

### 1. Enable Socket Mode
1. Go to https://api.slack.com/apps
2. Select your app → Socket Mode → Enable
3. Create App-Level Token with `connections:write` scope
4. Copy the token (starts with `xapp-`)

### 2. Event Subscriptions
1. Go to Event Subscriptions → Enable Events  
2. Subscribe to bot events: `message.channels`
3. No Request URL needed (Socket Mode handles this)

### 3. OAuth & Permissions
Add bot token scopes:
- `channels:read` - See channel list
- `channels:history` - Read message history  
- `chat:write` - Send messages (optional)
- `users:read` - Get user names

## ✅ Step 5: Test Everything

### 1. Test Database Connection
```bash
python3 -c "
from cloud_database_manager import CloudDatabaseManager
db = CloudDatabaseManager()
print('Health check:', db.health_check())
print('Statistics:', db.get_statistics())
"
```

### 2. Test Real-time Monitoring
```bash
python3 realtime_monitor.py
```

You should see:
```
🚀 Real-time Q&A Monitor initialized
🐘 Setting up PostgreSQL connection  
✅ PostgreSQL database initialized
✅ Connected to Slack via Socket Mode
🔍 Monitoring for new messages...
```

### 3. Test in Slack
1. Go to a channel where your bot is added
2. Ask a question: "How do I deploy this bot?"
3. Check bot logs for question detection
4. Have someone answer the question
5. Check database for stored Q&A pair

## 📊 Monitoring Your Production Bot

### Database Stats
```python
from cloud_database_manager import CloudDatabaseManager

db = CloudDatabaseManager()
stats = db.get_statistics()
print(f"Questions: {stats['questions']}")
print(f"Answers: {stats['answers']}")
print(f"Q&A Pairs: {stats['qa_pairs']}")
```

### Health Check Endpoint
```python
# Add to your bot for monitoring
@app.route('/health')
def health():
    db = CloudDatabaseManager()
    return db.health_check()
```

## 💡 Production Tips

### 1. Environment Variables
Never hardcode secrets. Use environment variables:
```bash
# Development
export DATABASE_URL="postgresql://..."

# Production (set in hosting platform)
DATABASE_URL=postgresql://prod-url-here
OPENAI_API_KEY=sk-prod-key-here
```

### 2. Error Handling
The new system includes:
- ✅ Database connection pooling
- ✅ Automatic retries  
- ✅ Graceful error handling
- ✅ Health monitoring

### 3. Scaling
Free tiers handle:
- **Neon**: 1GB data (~100k Q&A pairs)
- **Railway**: $5 credit/month
- **Typical usage**: Small team uses < $2/month

## 🚨 Troubleshooting

### "Connection refused"
- Check DATABASE_URL is correct
- Ensure database allows external connections
- Verify SSL mode is set correctly

### "Module not found: psycopg2"  
```bash
pip install psycopg2-binary
```

### "Table doesn't exist"
Tables are created automatically. If issues:
```python
from cloud_database_manager import CloudDatabaseManager
db = CloudDatabaseManager()
# Tables created automatically on first use
```

### "Too many connections"
The system uses connection pooling, but if issues:
```python
# In config_manager.py, reduce pool size
POSTGRES_POOL_SIZE = 5
```

## 🔄 Migration from SQLite

If you have existing SQLite data:

```python
# Export from SQLite
from database_manager import DatabaseManager as SQLiteDB
sqlite_db = SQLiteDB('./out/qa_database.db')
pairs = sqlite_db.get_qa_pairs(limit=10000)

# Import to PostgreSQL
from cloud_database_manager import CloudDatabaseManager
postgres_db = CloudDatabaseManager()
for pair in pairs:
    postgres_db.store_qa_pair(pair)
```

## 📈 Next Steps

1. **Deploy**: Get your bot running in the cloud
2. **Monitor**: Set up health checks and alerts
3. **Scale**: Upgrade database as team grows
4. **Enhance**: Add features like search, categories, etc.

Your Slack bot is now enterprise-ready with persistent, accessible cloud storage! 🎉