# 🤖 Slack Q&A Bot

Automatically detects questions and answers in your Slack workspace and stores them in a searchable database.

## 🚀 Quick Deploy to Render

### 1. Setup Environment
1. Copy `.env.example` to `.env`
2. Get your tokens:
   - **Slack**: Create app at https://api.slack.com/apps
   - **OpenAI**: Get API key from https://platform.openai.com/api-keys

### 2. Deploy to Render
1. Fork this repository 
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`  
5. Set start command: `python start.py`
6. Add environment variables from your `.env` file
7. Create PostgreSQL database in Render
8. Deploy!

## 🏗️ What's Included

```
├── config/           # Configuration management
├── core/            # Message processing & AI analysis  
├── database/        # SQLite & PostgreSQL support
├── start.py         # Main entry point for Render
├── realtime_monitor.py  # Real-time Socket Mode bot
├── qa_extractor.py  # Batch message processing
├── web_viewer.py    # Optional web dashboard
└── requirements.txt # Python dependencies
```

## 🔧 Local Development

```bash
# Setup
cp .env.example .env
# Add your API keys to .env

# Install dependencies  
pip install -r requirements.txt

# Run locally
python start.py
```

## 🌐 Features

- ✅ **Real-time monitoring** via Slack Socket Mode
- ✅ **AI-powered Q&A detection** using OpenAI
- ✅ **PostgreSQL database** for production  
- ✅ **SQLite fallback** for local development
- ✅ **Web dashboard** to view collected Q&A pairs
- ✅ **Export to CSV** for analysis
- ✅ **Duplicate prevention** 

## 📊 Usage

Once deployed, your bot will:
1. Monitor all Slack channels it has access to
2. Use AI to detect questions (confidence > 70%)  
3. Match answers to recent questions
4. Store Q&A pairs in PostgreSQL database
5. Provide web interface at your Render URL

## ⚙️ Configuration

Key settings in `config/config_manager.py`:
- `QUESTION_DETECTION_THRESHOLD = 0.7` - AI confidence for questions
- `ANSWER_DETECTION_THRESHOLD = 0.6` - AI confidence for answers  
- `ANSWER_TIMEOUT_HOURS = 24` - How long to wait for answers

## 🔐 Security

- All API keys stored as environment variables
- Database credentials managed by Render
- No secrets in code repository
- PostgreSQL database is private and encrypted

## 💰 Cost

**Free tier (first month):**
- Render: 750 hours free
- PostgreSQL: Included
- Total: $0

**After free tier:**
- ~$7-15/month total for small teams

## 🆘 Troubleshooting

**Bot not detecting messages:**
- Check Slack app has `channels:read` and `channels:history` scopes
- Ensure Socket Mode is enabled
- Verify `SLACK_APP_TOKEN` starts with `xapp-`

**Database connection issues:**
- Render auto-provides `DATABASE_URL` 
- Check PostgreSQL service is running
- Bot falls back to SQLite if PostgreSQL unavailable

**No Q&A pairs found:**
- AI threshold might be too high
- Try asking clear questions in monitored channels  
- Check OpenAI API key has credits

---

**Ready to build your team's knowledge base?** Deploy to Render in 5 minutes!