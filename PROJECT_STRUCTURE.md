# 📁 Project Structure

```
slackdump/
├── 📁 config/                    # Configuration management
│   ├── __init__.py
│   └── config_manager.py         # Environment and pipeline settings
│
├── 📁 core/                      # Core processing components
│   ├── __init__.py
│   ├── message_processor.py      # Message formatting utilities
│   ├── openai_analyzer.py        # AI-powered Q&A detection
│   └── slack_client.py           # Slack API interactions
│
├── 📁 database/                  # Database management
│   ├── __init__.py
│   ├── database_manager.py       # SQLite database (legacy)
│   └── cloud_database_manager.py # PostgreSQL/SQLite unified manager
│
├── 📁 docs/                      # Documentation
│   ├── AUTONOMOUS_ACCESS_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md       # Cloud deployment instructions
│   ├── PERMISSION_SOLUTIONS.md
│   └── README_QA_SYSTEM.md       # Main documentation
│
├── 📁 examples/                  # Usage examples and demos
│   ├── __init__.py
│   ├── example_database_usage.py # Database operations demo
│   └── example_usage.py          # Complete system demo
│
├── 📁 tests/                     # Test suites
│   ├── __init__.py
│   ├── test_autonomous_access.py
│   ├── test_channels.py
│   ├── test_database_only.py     # Database integration tests
│   ├── test_integration.py       # Full system tests
│   └── test_qa_system.py         # Unit tests
│
├── 📁 out/                       # Output files and database
│   ├── qa_database.db           # SQLite database (if used)
│   ├── example_qa.db            # Test databases
│   ├── *.csv                    # Exported Q&A data
│   └── *.jsonl                  # Raw extraction results
│
├── 🚀 MAIN ENTRY POINTS
├── realtime_monitor.py          # Real-time Socket Mode monitoring
├── qa_extractor.py              # Batch processing of messages
├── run_complete_pipeline.py     # Full pipeline execution
│
├── 🔧 UTILITY SCRIPTS
├── add_bot_to_private_channels.py
├── setup_admin_bot.py
├── setup_autonomous_access.py
├── faq_generator.py
│
├── ⚙️ CONFIGURATION FILES
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container deployment
├── cronjob.yaml                # Scheduled execution
│
└── 📄 PROJECT FILES
    ├── __init__.py             # Package initialization
    └── PROJECT_STRUCTURE.md    # This file
```

## 🎯 Main Components

### Entry Points
- **`realtime_monitor.py`** - Start real-time Q&A monitoring
- **`qa_extractor.py`** - Run batch processing on historical messages
- **`run_complete_pipeline.py`** - Execute full extraction pipeline

### Core System
- **`config/config_manager.py`** - All configuration and environment settings
- **`database/cloud_database_manager.py`** - Production-ready database with PostgreSQL support
- **`core/openai_analyzer.py`** - AI-powered question/answer detection
- **`core/slack_client.py`** - Slack API integration with rate limiting

### Testing & Examples
- **`tests/test_qa_system.py`** - Comprehensive unit tests
- **`examples/example_database_usage.py`** - Database operations demo
- **`docs/DEPLOYMENT_GUIDE.md`** - Production deployment guide

## 🚀 Quick Start

### 1. Real-time Monitoring
```bash
python realtime_monitor.py
```

### 2. Batch Processing
```bash
python qa_extractor.py
```

### 3. Run Tests
```bash
python tests/test_qa_system.py
```

### 4. Database Demo
```bash
python examples/example_database_usage.py
```

## 📦 Import Structure

### From Main Directory
```python
# Real-time monitoring
from realtime_monitor import RealtimeQAMonitor

# Batch processing
from qa_extractor import QAExtractor

# Database operations
from database.cloud_database_manager import CloudDatabaseManager

# Configuration
from config.config_manager import PipelineConfig
```

### From Subdirectories
```python
# Core components
from core.openai_analyzer import OpenAIAnalyzer
from core.slack_client import SlackDataFetcher
from core.message_processor import MessageProcessor

# Database (choose one)
from database.cloud_database_manager import CloudDatabaseManager  # Production
from database.database_manager import DatabaseManager             # Local SQLite
```

## 🔄 Migration Guide

### Old Import → New Import
```python
# OLD
from database_manager import DatabaseManager
from config_manager import PipelineConfig
from openai_analyzer import OpenAIAnalyzer

# NEW
from database.cloud_database_manager import CloudDatabaseManager as DatabaseManager
from config.config_manager import PipelineConfig
from core.openai_analyzer import OpenAIAnalyzer
```

## 📋 Development Workflow

1. **Configuration**: Modify `config/config_manager.py`
2. **Database**: Use `database/cloud_database_manager.py` for production
3. **AI Analysis**: Enhance `core/openai_analyzer.py`
4. **Testing**: Add tests to `tests/` directory
5. **Documentation**: Update files in `docs/` directory

This structure provides clear separation of concerns while maintaining backward compatibility with the existing codebase.