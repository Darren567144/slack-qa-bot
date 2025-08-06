#!/usr/bin/env python
"""
Usage examples for the Q&A detection and storage system.
"""
import os
from datetime import datetime
from pathlib import Path

# Import our modules
from database_manager import DatabaseManager
from openai_analyzer import OpenAIAnalyzer
from qa_extractor import QAExtractor
from config_manager import PipelineConfig


def example_database_operations():
    """Example of basic database operations."""
    print("📊 Example: Database Operations")
    print("-" * 40)
    
    # Initialize database
    db_manager = DatabaseManager("./out/example_qa.db")
    
    # Store a Q&A pair (backward compatibility with existing system)
    qa_pair = {
        'question': 'How do I handle environment variables in Python?',
        'answer': 'Use os.environ.get("VAR_NAME") or python-dotenv for .env files',
        'question_user': 'PythonLearner',
        'answer_user': 'PythonExpert',
        'channel': 'python-help',
        'timestamp': datetime.now().isoformat(),
        'confidence_score': 0.92
    }
    
    qa_id = db_manager.store_qa_pair(qa_pair)
    print(f"✅ Stored Q&A pair with ID: {qa_id}")
    
    # Store individual question (new real-time system)
    question_data = {
        'text': 'What is the best way to structure a FastAPI project?',
        'user_id': 'U123456',
        'user_name': 'WebDeveloper',
        'channel_id': 'fastapi-help',
        'timestamp': datetime.now(),
        'message_ts': '1700000001.123456',
        'confidence_score': 0.88,
        'metadata': {
            'question_type': 'direct',
            'detected_at': datetime.now().isoformat()
        }
    }
    
    question_id = db_manager.store_question(question_data)
    print(f"✅ Stored question with ID: {question_id}")
    
    # Store corresponding answer
    answer_data = {
        'text': 'Use a directory structure with app/, models/, routes/, and services/ folders',
        'user_id': 'U789012',
        'user_name': 'FastAPIExpert',
        'channel_id': 'fastapi-help',
        'timestamp': datetime.now(),
        'message_ts': '1700000002.789012',
        'confidence_score': 0.95,
        'metadata': {
            'answer_quality': 'direct',
            'detected_at': datetime.now().isoformat()
        }
    }
    
    answer_id = db_manager.store_answer(answer_data, question_id)
    print(f"✅ Stored answer with ID: {answer_id} (linked to question {question_id})")
    
    # Get statistics
    stats = db_manager.get_statistics()
    print(f"📈 Database stats: {stats['questions']} questions, {stats['answers']} answers, {stats['qa_pairs']} Q&A pairs")
    
    # Find recent unanswered questions
    unanswered = db_manager.find_recent_questions('python-help', hours=24)
    print(f"❓ Found {len(unanswered)} unanswered questions in python-help")
    
    # Export to CSV
    db_manager.export_to_csv("./out/example_export.csv")
    print("✅ Exported data to CSV")
    
    return db_manager


def example_batch_processing():
    """Example of batch processing existing messages."""
    print("\n🔄 Example: Batch Processing")
    print("-" * 40)
    
    # Note: This requires valid Slack tokens
    # qa_extractor = QAExtractor()
    # 
    # # Extract Q&A pairs from recent messages (up to 100 per channel)
    # all_pairs, raw_file = qa_extractor.extract_qa_pairs(max_messages_per_channel=100)
    # print(f"✅ Extracted {len(all_pairs)} Q&A pairs")
    # 
    # # Deduplicate results
    # unique_pairs, deduplicated_file = qa_extractor.deduplicate_qa_pairs(raw_file)
    # print(f"✅ After deduplication: {len(unique_pairs)} unique pairs")
    
    print("📝 Note: Batch processing requires valid SLACK_TOKEN and OPENAI_API_KEY")
    print("   Set these in environment variables or .env file")
    print("   Example usage:")
    print("   export SLACK_TOKEN='xoxb-your-bot-token'")
    print("   export OPENAI_API_KEY='sk-your-openai-key'")
    print("   python qa_extractor.py")


def example_realtime_monitoring():
    """Example of real-time monitoring setup."""
    print("\n⚡ Example: Real-time Monitoring")
    print("-" * 40)
    
    print("📝 Real-time monitoring requires Socket Mode setup:")
    print("   1. Create Slack app at https://api.slack.com/apps")
    print("   2. Enable Socket Mode in app settings")
    print("   3. Subscribe to 'message.channels' events")
    print("   4. Install app to your workspace")
    print("   5. Set environment variables:")
    print("      export SLACK_BOT_TOKEN='xoxb-your-bot-token'")
    print("      export SLACK_APP_TOKEN='xapp-your-app-token'")
    print("      export OPENAI_API_KEY='sk-your-openai-key'")
    print("   6. Run: python realtime_monitor.py")
    print()
    print("🔧 The real-time monitor will:")
    print("   - Connect to Slack via Socket Mode")
    print("   - Listen for new messages")
    print("   - Detect questions using OpenAI")
    print("   - Match answers to recent questions")
    print("   - Store everything in SQLite database")
    print("   - Avoid reprocessing messages")


def example_openai_analysis():
    """Example of OpenAI-powered Q&A analysis."""
    print("\n🤖 Example: OpenAI Analysis")
    print("-" * 40)
    
    # Note: This requires a valid OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("📝 Note: Set OPENAI_API_KEY environment variable to test OpenAI features")
        return
    
    analyzer = OpenAIAnalyzer()
    
    # Test question detection
    test_messages = [
        "How do I set up Docker for my Python app?",
        "Thanks for the help!",
        "Can someone explain async/await in Python?",
        "The server is running on port 8000",
        "What's the best way to handle database migrations?"
    ]
    
    print("🔍 Testing question detection:")
    for msg in test_messages:
        try:
            result = analyzer.is_question(msg)
            is_q = result.get('is_question', False)
            confidence = result.get('confidence', 0)
            q_type = result.get('question_type', 'none')
            
            status = "❓" if is_q else "💬"
            print(f"   {status} \"{msg[:40]}...\" -> {is_q} (confidence: {confidence:.2f}, type: {q_type})")
        except Exception as e:
            print(f"   ❌ Error analyzing: {e}")
    
    # Test answer detection
    print("\n🔍 Testing answer detection:")
    question = "How do I set up Docker for my Python app?"
    potential_answers = [
        "Create a Dockerfile with Python base image and copy your requirements.txt",
        "I'm not sure about that",
        "Use docker-compose for development with volume mounts for hot reloading"
    ]
    
    for answer in potential_answers:
        try:
            result = analyzer.is_answer_to_question(question, answer)
            is_answer = result.get('is_answer', False)
            confidence = result.get('confidence', 0)
            quality = result.get('answer_quality', 'none')
            
            status = "💡" if is_answer else "❌"
            print(f"   {status} \"{answer[:40]}...\" -> {is_answer} (confidence: {confidence:.2f}, quality: {quality})")
        except Exception as e:
            print(f"   ❌ Error analyzing: {e}")


def example_configuration():
    """Example of configuration options."""
    print("\n⚙️  Example: Configuration")
    print("-" * 40)
    
    config = PipelineConfig()
    
    print("📊 Current configuration:")
    print(f"   Max messages per channel: {config.MAX_MESSAGES_PER_CHANNEL}")
    print(f"   Context window size: {config.CONTEXT_WINDOW_SIZE}")
    print(f"   OpenAI model: {config.OPENAI_MODEL}")
    print(f"   Question detection threshold: {config.QUESTION_DETECTION_THRESHOLD}")
    print(f"   Answer detection threshold: {config.ANSWER_DETECTION_THRESHOLD}")
    print(f"   Database path: {config.DATABASE_PATH}")
    print(f"   Real-time enabled: {config.REALTIME_ENABLED}")
    print(f"   Message buffer size: {config.MESSAGE_BUFFER_SIZE}")
    print(f"   Answer timeout: {config.ANSWER_TIMEOUT_HOURS} hours")
    
    print("\n🔧 To customize configuration:")
    print("   1. Modify values in config_manager.py")
    print("   2. Or set environment variables:")
    print("      export OPENAI_MODEL='gpt-4'")
    print("   3. Or create custom PipelineConfig subclass")


def main():
    """Run all examples."""
    print("🚀 Q&A Detection and Storage System - Usage Examples")
    print("=" * 60)
    
    try:
        # Database operations example
        db_manager = example_database_operations()
        
        # Other examples
        example_batch_processing()
        example_realtime_monitoring()
        example_openai_analysis()
        example_configuration()
        
        print("\n" + "=" * 60)
        print("🎉 Examples completed successfully!")
        print("✅ Database operations")
        print("✅ Batch processing info")
        print("✅ Real-time monitoring setup")
        print("✅ OpenAI analysis")
        print("✅ Configuration options")
        
        # Clean up example database
        if db_manager and Path(db_manager.db_path).exists():
            print(f"\n📁 Example database created at: {db_manager.db_path}")
            print("   You can explore it with any SQLite browser")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()