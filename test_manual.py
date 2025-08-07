#!/usr/bin/env python
"""
Manual testing script for the QA Bot with sample data.
Run this script to test the bot with realistic conversation data.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from database.database_manager import DatabaseManager
from core.message_processor import MessageProcessor
from core.openai_analyzer import OpenAIAnalyzer


def create_sample_conversations():
    """Create realistic sample conversations for testing."""
    return [
        {
            "name": "Deployment Help",
            "messages": [
                {"user": "U001", "text": "Hey team, I'm struggling with deploying our app to production. Any suggestions?", "ts": "1640995200.001", "user_name": "Alice"},
                {"user": "U002", "text": "What platform are you trying to deploy to?", "ts": "1640995220.001", "user_name": "Bob"},
                {"user": "U001", "text": "I was thinking either Heroku or Render. Which one would you recommend?", "ts": "1640995240.001", "user_name": "Alice"},
                {"user": "U002", "text": "I'd go with Render. It has better free tier limits and easier Python setup.", "ts": "1640995280.001", "user_name": "Bob"},
                {"user": "U003", "text": "Agreed! Plus Render auto-scales better than Heroku's free tier.", "ts": "1640995320.001", "user_name": "Charlie"},
                {"user": "U001", "text": "Perfect! How do I get started with Render?", "ts": "1640995360.001", "user_name": "Alice"},
                {"user": "U002", "text": "Just connect your GitHub repo and set your build/start commands. Super simple!", "ts": "1640995400.001", "user_name": "Bob"}
            ]
        },
        {
            "name": "Database Issues",
            "messages": [
                {"user": "U004", "text": "Our PostgreSQL database is running slow. Anyone know how to optimize queries?", "ts": "1641000000.001", "user_name": "David"},
                {"user": "U005", "text": "Have you checked your indexes? Missing indexes are usually the culprit.", "ts": "1641000060.001", "user_name": "Eve"},
                {"user": "U004", "text": "Good point. How do I check which queries need indexes?", "ts": "1641000120.001", "user_name": "David"},
                {"user": "U005", "text": "Use EXPLAIN ANALYZE on your slow queries. It'll show you where the bottlenecks are.", "ts": "1641000180.001", "user_name": "Eve"},
                {"user": "U006", "text": "Also consider using pg_stat_statements to find your slowest queries automatically.", "ts": "1641000240.001", "user_name": "Frank"}
            ]
        },
        {
            "name": "Code Review Process",
            "messages": [
                {"user": "U007", "text": "What's our process for code reviews? I'm new to the team.", "ts": "1641010000.001", "user_name": "Grace"},
                {"user": "U008", "text": "We use GitHub PRs. Just push your branch and create a pull request.", "ts": "1641010060.001", "user_name": "Henry"},
                {"user": "U007", "text": "Do I need specific reviewers or can anyone review?", "ts": "1641010120.001", "user_name": "Grace"},
                {"user": "U008", "text": "Add at least 2 reviewers from your squad. Check our team docs for the squad assignments.", "ts": "1641010180.001", "user_name": "Henry"},
                {"user": "U009", "text": "And make sure all tests pass before requesting review!", "ts": "1641010240.001", "user_name": "Ivy"}
            ]
        },
        {
            "name": "Testing Strategies",
            "messages": [
                {"user": "U010", "text": "How should I test this new API endpoint?", "ts": "1641020000.001", "user_name": "Jack"},
                {"user": "U011", "text": "Write unit tests for the business logic and integration tests for the full endpoint.", "ts": "1641020060.001", "user_name": "Kate"},
                {"user": "U010", "text": "What testing framework do we use?", "ts": "1641020120.001", "user_name": "Jack"},
                {"user": "U011", "text": "pytest for Python. We have examples in the tests/ directory.", "ts": "1641020180.001", "user_name": "Kate"},
                {"user": "U012", "text": "Don't forget to test error cases and edge conditions too!", "ts": "1641020240.001", "user_name": "Leo"}
            ]
        },
        {
            "name": "Random Chat", 
            "messages": [
                {"user": "U013", "text": "Good morning everyone!", "ts": "1641030000.001", "user_name": "Mike"},
                {"user": "U014", "text": "Morning! How was your weekend?", "ts": "1641030060.001", "user_name": "Nina"},
                {"user": "U013", "text": "Great! Went hiking. You?", "ts": "1641030120.001", "user_name": "Mike"},
                {"user": "U014", "text": "Just relaxed at home. Ready for the week ahead!", "ts": "1641030180.001", "user_name": "Nina"}
            ]
        }
    ]


def run_test_without_openai():
    """Test the system with mock OpenAI responses (no API calls)."""
    print("🧪 Testing QA Bot WITHOUT OpenAI API calls...")
    print("=" * 50)
    
    # Create test database
    db_manager = DatabaseManager("test_qa_database.db")
    message_processor = MessageProcessor()
    
    # Create sample conversations
    conversations = create_sample_conversations()
    
    # Mock Q&A pairs that would be extracted
    mock_qa_pairs = [
        {
            "question": "Which platform would you recommend for deployment, Heroku or Render?",
            "answer": "I'd go with Render. It has better free tier limits and easier Python setup.",
            "question_user": "Alice",
            "answer_user": "Bob",
            "conversation": "Deployment Help"
        },
        {
            "question": "How do I get started with Render?",
            "answer": "Just connect your GitHub repo and set your build/start commands. Super simple!",
            "question_user": "Alice", 
            "answer_user": "Bob",
            "conversation": "Deployment Help"
        },
        {
            "question": "How do I check which queries need indexes?",
            "answer": "Use EXPLAIN ANALYZE on your slow queries. It'll show you where the bottlenecks are.",
            "question_user": "David",
            "answer_user": "Eve",
            "conversation": "Database Issues"
        },
        {
            "question": "What's our process for code reviews?",
            "answer": "We use GitHub PRs. Just push your branch and create a pull request.",
            "question_user": "Grace",
            "answer_user": "Henry",
            "conversation": "Code Review Process"
        },
        {
            "question": "What testing framework do we use?",
            "answer": "pytest for Python. We have examples in the tests/ directory.",
            "question_user": "Jack",
            "answer_user": "Kate",
            "conversation": "Testing Strategies"
        }
    ]
    
    print(f"📝 Processing {len(conversations)} sample conversations...")
    
    # Process conversations and store mock Q&A pairs
    for i, conversation in enumerate(conversations):
        print(f"\n📋 Processing: {conversation['name']}")
        
        # Create conversation windows (this tests the message processor)
        user_names = {msg["user"]: msg["user_name"] for msg in conversation["messages"]}
        windows = message_processor.create_conversation_windows(conversation["messages"], user_names)
        
        print(f"   Created {len(windows)} conversation windows")
        
        # Store relevant mock Q&A pairs for this conversation
        relevant_pairs = [pair for pair in mock_qa_pairs if pair["conversation"] == conversation["name"]]
        
        for pair in relevant_pairs:
            qa_data = {
                'question': pair['question'],
                'answer': pair['answer'],
                'question_user': pair['question_user'],
                'answer_user': pair['answer_user'],
                'channel': f"#{conversation['name'].lower().replace(' ', '-')}",
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.85
            }
            
            pair_id = db_manager.store_qa_pair(qa_data)
            print(f"   ✅ Stored Q&A pair: {pair['question'][:50]}...")
    
    # Display results
    print(f"\n📊 Test Results:")
    stats = db_manager.get_statistics()
    print(f"   Total Q&A pairs stored: {stats['qa_pairs']}")
    print(f"   Database location: {stats['database_path']}")
    
    # Show sample Q&A pairs
    print(f"\n🔍 Sample Q&A pairs extracted:")
    qa_pairs = db_manager.get_qa_pairs(limit=3)
    for i, pair in enumerate(qa_pairs, 1):
        print(f"\n   {i}. Q: {pair['question']}")
        print(f"      A: {pair['answer']}")
        print(f"      Users: {pair['question_user']} → {pair['answer_user']}")
        print(f"      Channel: {pair['channel']}")
    
    return db_manager


def run_test_with_openai():
    """Test the system with real OpenAI API calls."""
    print("\n🤖 Testing QA Bot WITH OpenAI API calls...")
    print("=" * 50)
    
    # Check for OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please set your OpenAI API key to run this test:")
        print("   export OPENAI_API_KEY='your-key-here'")
        return None
    
    try:
        from core.openai_analyzer import OpenAIAnalyzer
        
        # Create components
        db_manager = DatabaseManager("test_qa_database_openai.db")
        message_processor = MessageProcessor()
        openai_analyzer = OpenAIAnalyzer()
        
        # Use a smaller conversation for API testing
        test_conversation = create_sample_conversations()[0]  # Deployment Help
        
        print(f"📝 Processing conversation: {test_conversation['name']}")
        
        # Create conversation windows
        user_names = {msg["user"]: msg["user_name"] for msg in test_conversation["messages"]}
        windows = message_processor.create_conversation_windows(test_conversation["messages"], user_names)
        
        print(f"   Created {len(windows)} conversation windows")
        
        # Process each window with OpenAI
        total_pairs = 0
        for i, window in enumerate(windows):
            print(f"\n   🔍 Analyzing window {i+1} with OpenAI...")
            print(f"      Content preview: {window['formatted_text'][:100]}...")
            
            # Extract Q&A pairs using OpenAI
            qa_pairs = openai_analyzer.extract_qa_pairs_from_conversation(window['formatted_text'])
            
            print(f"      Found {len(qa_pairs)} Q&A pairs")
            
            # Store the pairs
            for pair in qa_pairs:
                qa_data = {
                    'question': pair.get('question', ''),
                    'answer': pair.get('answer', ''),
                    'question_user': pair.get('question_user', ''),
                    'answer_user': pair.get('answer_user', ''),
                    'channel': '#deployment-help',
                    'timestamp': datetime.now().isoformat(),
                    'confidence_score': 0.8
                }
                
                db_manager.store_qa_pair(qa_data)
                total_pairs += 1
                print(f"      ✅ Stored: {pair.get('question', '')[:50]}...")
        
        # Display results
        print(f"\n📊 OpenAI Test Results:")
        stats = db_manager.get_statistics()
        print(f"   Total Q&A pairs extracted: {stats['qa_pairs']}")
        
        # Show extracted pairs
        if stats['qa_pairs'] > 0:
            print(f"\n🔍 Q&A pairs extracted by OpenAI:")
            qa_pairs = db_manager.get_qa_pairs()
            for i, pair in enumerate(qa_pairs, 1):
                print(f"\n   {i}. Q: {pair['question']}")
                print(f"      A: {pair['answer']}")
                print(f"      Users: {pair['question_user']} → {pair['answer_user']}")
        
        return db_manager
        
    except Exception as e:
        print(f"❌ Error testing with OpenAI: {e}")
        return None


def run_individual_message_analysis():
    """Test individual message analysis (question/answer detection)."""
    print("\n🔍 Testing Individual Message Analysis...")
    print("=" * 50)
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ Skipping individual analysis test - no OpenAI API key")
        return
    
    try:
        from core.openai_analyzer import OpenAIAnalyzer
        openai_analyzer = OpenAIAnalyzer()
        
        test_messages = [
            "How do I deploy this app to production?",  # Clear question
            "You can use Render or Heroku for deployment",  # Answer
            "Thanks for the help!",  # Not a question
            "What's the best way to test React components?",  # Question
            "I recommend using Jest and React Testing Library",  # Answer
            "Good morning everyone!",  # Greeting (not a question)
            "Can someone help me with this error?",  # Implicit question
        ]
        
        print("🧪 Testing question detection:")
        for msg in test_messages:
            result = openai_analyzer.is_question(msg)
            status = "✅ QUESTION" if result['is_question'] else "❌ NOT QUESTION"
            confidence = result['confidence']
            print(f"   {status} ({confidence:.2f}): {msg}")
        
        print("\n🧪 Testing answer matching:")
        question = "How do I deploy this app?"
        potential_answers = [
            "You can use Render or Heroku",  # Good answer
            "I don't know",  # Weak answer
            "What's for lunch?",  # Irrelevant
            "Try using Docker containers with these platforms"  # Good answer
        ]
        
        for answer in potential_answers:
            result = openai_analyzer.is_answer_to_question(question, answer)
            status = "✅ ANSWER" if result['is_answer'] else "❌ NOT ANSWER"
            confidence = result['confidence']
            quality = result['answer_quality']
            print(f"   {status} ({confidence:.2f}, {quality}): {answer}")
            
    except Exception as e:
        print(f"❌ Error in individual message analysis: {e}")


def main():
    """Run all manual tests."""
    print("🚀 Starting Manual QA Bot Testing")
    print("=" * 50)
    
    # Test 1: Without OpenAI (using mock data)
    db1 = run_test_without_openai()
    
    # Test 2: With OpenAI (real API calls)
    db2 = run_test_with_openai()
    
    # Test 3: Individual message analysis
    run_individual_message_analysis()
    
    print("\n" + "=" * 50)
    print("🎉 Manual testing complete!")
    print("\nFiles created:")
    if db1:
        print(f"   📁 Mock test database: {db1.db_path}")
    if db2:
        print(f"   📁 OpenAI test database: {db2.db_path}")
    
    print("\n💡 Next steps:")
    print("   1. Run unit tests: pytest")
    print("   2. Check the web viewer to see extracted Q&A pairs")
    print("   3. Test with your actual Slack workspace")
    print("   4. Export results: python -c 'from database.database_manager import DatabaseManager; db=DatabaseManager(\"test_qa_database.db\"); db.export_to_csv(\"results.csv\")'")


if __name__ == "__main__":
    main()