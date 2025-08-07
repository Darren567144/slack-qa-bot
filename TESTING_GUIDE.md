# 🧪 QA Bot Testing Guide

Complete guide for testing your Slack Q&A Bot to ensure it works correctly before deployment.

## 📋 Quick Start Testing

### 1. Install Test Dependencies
```bash
cd qa-slackbot
pip install pytest pytest-mock pytest-cov
```

### 2. Run All Tests
```bash
# Run unit tests
pytest

# Run with coverage report
pytest --cov=core --cov=database --cov-report=html

# Run specific test file
pytest test_openai_analyzer.py -v
```

### 3. Manual Testing with Sample Data
```bash
# Test without OpenAI API (uses mock data)
python test_manual.py

# Test with real OpenAI API (requires OPENAI_API_KEY)
export OPENAI_API_KEY="your-api-key-here"
python test_manual.py
```

## 🏗️ Test Structure

### Unit Tests
- **`test_message_processor.py`** - Message formatting and conversation windows
- **`test_openai_analyzer.py`** - Q&A extraction and analysis (mocked)
- **`test_database_manager.py`** - Database operations and storage

### Integration Tests
- **`test_integration.py`** - Complete pipeline from messages to stored Q&A pairs

### Manual Testing
- **`test_manual.py`** - Interactive testing with realistic sample data

## 📊 Test Results Interpretation

### Unit Test Results
```bash
pytest -v
```
**Expected Output:**
- All tests should pass (green checkmarks)
- Coverage should be > 80%
- No import errors or missing dependencies

**Common Issues:**
- ❌ `ImportError` → Run `pip install -r requirements.txt`
- ❌ `FileNotFoundError` → Run tests from `qa-slackbot/` directory

### Manual Test Results
```bash
python test_manual.py
```
**Expected Output:**
```
🧪 Testing QA Bot WITHOUT OpenAI API calls...
📝 Processing 5 sample conversations...
📊 Test Results:
   Total Q&A pairs stored: 5
🔍 Sample Q&A pairs extracted:
   1. Q: Which platform would you recommend for deployment...
      A: I'd go with Render. It has better free tier limits...
```

## 🤖 Testing with OpenAI API

### Setup
```bash
# Get API key from https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-your-key-here"

# Test individual message analysis
python test_manual.py
```

### Expected Behavior
- **Question Detection:** Should identify questions with >70% confidence
- **Answer Matching:** Should link relevant answers to questions
- **Q&A Extraction:** Should extract meaningful pairs from conversations

### Cost Estimation
- Manual test script: ~$0.01-0.05 per run
- Unit tests: Free (mocked)
- Production use: ~$5-20/month depending on message volume

## 🔍 Testing Different Scenarios

### 1. Question Types
Test these message patterns:
```python
# Direct questions
"How do I deploy this app?"
"What's the best database for this project?"

# Implicit questions  
"I need help with authentication"
"Can someone explain JWT tokens?"

# Help requests
"Anyone know how to fix this error?"
"Struggling with Docker setup"
```

### 2. Answer Quality
```python
# Direct answers
Q: "How do I deploy?" 
A: "Use 'git push heroku main' command"

# Partial answers
Q: "How do I deploy?"
A: "I use Heroku, works well"

# Irrelevant responses
Q: "How do I deploy?"
A: "Good morning everyone!"
```

### 3. Edge Cases
- Very short messages
- Code snippets in messages  
- Multiple questions in one message
- Delayed answers (24+ hours later)
- Multiple people answering the same question

## 📈 Performance Testing

### Database Performance
```bash
# Test with large dataset
python -c "
from test_manual import create_sample_conversations
from database.database_manager import DatabaseManager
import time

db = DatabaseManager('perf_test.db')
start = time.time()

# Insert 1000 Q&A pairs
for i in range(1000):
    qa_data = {
        'question': f'Question {i}?',
        'answer': f'Answer {i}',
        'channel': '#test',
        'timestamp': '2023-01-01T10:00:00'
    }
    db.store_qa_pair(qa_data)

end = time.time()
print(f'Inserted 1000 pairs in {end-start:.2f}s')
print(f'Database stats: {db.get_statistics()}')
"
```

### Memory Usage
```bash
# Monitor memory during processing
python -m memory_profiler test_manual.py
```

## 🚦 Deployment Testing

### 1. Local Environment Test
```bash
# Test complete startup process
python start.py
```
**Should see:**
```
✅ All required environment variables found
🐘 Using PostgreSQL database: postgresql://...
🎯 Starting real-time monitoring...
```

### 2. Database Connection Test
```bash
# Test PostgreSQL connection
python -c "
from database.cloud_database_manager import CloudDatabaseManager
try:
    db = CloudDatabaseManager()
    stats = db.get_statistics()
    print('✅ PostgreSQL connection successful')
    print(f'Stats: {stats}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### 3. Slack API Test
```bash
# Test Slack connection (requires tokens)
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_APP_TOKEN="xapp-your-token"

python -c "
from core.slack_client import SlackClient
try:
    client = SlackClient()
    print('✅ Slack connection successful')
except Exception as e:
    print(f'❌ Slack connection failed: {e}')
"
```

## 🐛 Troubleshooting

### Common Test Failures

**1. OpenAI API Errors**
```bash
❌ OpenAI API error: Invalid API key
```
**Solution:** Check your `OPENAI_API_KEY` environment variable

**2. Database Errors**
```bash
❌ SQLite database locked
```
**Solution:** Close any other connections to test databases

**3. Import Errors**
```bash
❌ ModuleNotFoundError: No module named 'core'
```
**Solution:** Run tests from the `qa-slackbot/` directory

**4. Test Data Issues**
```bash
❌ AssertionError: Expected 2 Q&A pairs, got 0
```
**Solution:** Check OpenAI API key and model availability

### Debug Mode Testing
```bash
# Run tests with debug output
pytest -v -s --tb=long

# Test with logging enabled
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from test_manual import main
main()
"
```

## ✅ Testing Checklist

### Before Deployment
- [ ] All unit tests pass (`pytest`)
- [ ] Manual test extracts Q&A pairs (`python test_manual.py`)
- [ ] Database operations work correctly
- [ ] OpenAI integration functions (if using real API)
- [ ] No import errors or missing dependencies
- [ ] Test database files created successfully

### After Deployment
- [ ] Bot connects to Slack workspace
- [ ] Real messages are processed correctly
- [ ] Q&A pairs appear in web dashboard
- [ ] Database stores data persistently
- [ ] Export functionality works
- [ ] No memory leaks or performance issues

### Regular Monitoring
- [ ] Check Q&A pair quality weekly
- [ ] Monitor OpenAI API usage and costs
- [ ] Verify database performance
- [ ] Test backup and recovery procedures

## 📊 Success Metrics

**Good Results:**
- Unit tests: 100% pass rate
- Q&A extraction: >70% accuracy on sample conversations
- Response time: <2 seconds per message
- Database operations: <100ms per query

**Warning Signs:**
- Many false positives (non-questions detected as questions)
- Irrelevant answers matched to questions
- High OpenAI API costs (>$50/month for small team)
- Slow database performance (>1s per query)

## 🚀 Next Steps

After successful testing:

1. **Deploy to Production**
   ```bash
   git push origin main  # Deploy to Render/Heroku
   ```

2. **Monitor Live Performance**
   - Check web dashboard daily
   - Review Q&A quality weekly
   - Monitor API costs monthly

3. **Iterate and Improve**
   - Adjust confidence thresholds based on results
   - Add more test cases for edge scenarios
   - Implement additional quality filters

---

**Need Help?** 
- Check existing Q&A pairs in your database
- Review logs for error messages
- Test with simpler conversations first
- Gradually increase complexity