#!/usr/bin/env python
"""
Real-time Slack message monitoring and Q&A detection using Socket Mode.
"""
import time
import threading
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional

from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.web import WebClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from config.config_manager import get_required_env_vars, PipelineConfig
from database.database_manager import DatabaseManager
from core.openai_analyzer import OpenAIAnalyzer
from core.message_processor import MessageProcessor


class RealtimeQAMonitor:
    """Real-time Q&A detection and storage using Slack Socket Mode."""
    
    def __init__(self):
        env_vars = get_required_env_vars()
        self.config = PipelineConfig()
        
        # Initialize clients
        self.web_client = WebClient(token=env_vars['SLACK_TOKEN'])
        self.socket_client = SocketModeClient(
            app_token=env_vars['SLACK_APP_TOKEN'],
            web_client=self.web_client
        )
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.openai_analyzer = OpenAIAnalyzer()
        self.message_processor = MessageProcessor()
        
        # Message buffers for context (channel_id -> deque of messages)
        self.message_buffers: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.config.MESSAGE_BUFFER_SIZE)
        )
        
        # User name cache
        self.user_cache: Dict[str, str] = {}
        
        # Processing queue to avoid blocking Socket Mode
        self.processing_queue = deque()
        self.processing_thread = None
        self.running = False
        
        print(f"🚀 Real-time Q&A Monitor initialized")
        print(f"   Database: {self.db_manager.db_path}")
        print(f"   Question threshold: {self.config.QUESTION_DETECTION_THRESHOLD}")
        print(f"   Answer threshold: {self.config.ANSWER_DETECTION_THRESHOLD}")
    
    def get_user_name(self, user_id: str) -> str:
        """Get user name with caching."""
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        
        try:
            resp = self.web_client.users_info(user=user_id)
            name = resp["user"]["real_name"] or resp["user"]["name"]
            self.user_cache[user_id] = name
            return name
        except Exception as e:
            name = f"User{user_id[-4:]}"
            self.user_cache[user_id] = name
            return name
    
    def handle_message_event(self, request: SocketModeRequest):
        """Handle incoming message events."""
        if request.type == "events_api":
            event = request.payload.get("event", {})
            
            if event.get("type") == "message" and event.get("subtype") is None:
                # Only process regular messages (not bot messages, edits, etc.)
                channel_id = event.get("channel")
                user_id = event.get("user")
                message_text = event.get("text", "").strip()
                message_ts = event.get("ts")
                
                if channel_id and user_id and message_text and message_ts:
                    # Add to processing queue
                    message_data = {
                        "channel_id": channel_id,
                        "user_id": user_id,
                        "text": message_text,
                        "ts": message_ts,
                        "timestamp": datetime.fromtimestamp(float(message_ts))
                    }
                    
                    self.processing_queue.append(message_data)
                    print(f"📥 Queued message from {user_id} in {channel_id}: {message_text[:50]}...")
        
        # Acknowledge the request
        response = SocketModeResponse(envelope_id=request.envelope_id)
        self.socket_client.send_socket_mode_response(response)
    
    def process_message_queue(self):
        """Process queued messages in background thread."""
        while self.running:
            try:
                if self.processing_queue:
                    message_data = self.processing_queue.popleft()
                    
                    # Add delay to avoid processing messages that might be edited
                    time.sleep(self.config.PROCESS_MESSAGE_DELAY)
                    
                    # Check if already processed
                    if not self.db_manager.is_message_processed(message_data["ts"]):
                        self.process_single_message(message_data)
                        self.db_manager.mark_message_processed(message_data["ts"], message_data["channel_id"])
                else:
                    time.sleep(0.1)  # Short sleep when queue is empty
                    
            except Exception as e:
                print(f"❌ Error processing message queue: {e}")
                time.sleep(1)
    
    def process_single_message(self, message_data: Dict):
        """Process a single message for Q&A detection."""
        channel_id = message_data["channel_id"]
        user_id = message_data["user_id"]
        message_text = message_data["text"]
        message_ts = message_data["ts"]
        timestamp = message_data["timestamp"]
        
        # Get user name
        user_name = self.get_user_name(user_id)
        
        # Add to message buffer
        self.message_buffers[channel_id].append(message_data)
        
        print(f"🔍 Processing message from {user_name} in {channel_id}")
        
        # Check if it's a question
        question_analysis = self.openai_analyzer.is_question(message_text)
        
        if question_analysis.get("is_question", False):
            # Always store questions regardless of confidence threshold
            
            print(f"❓ Detected question (confidence: {question_analysis['confidence']:.2f}): {message_text[:100]}...")
            
            # Check for similar existing questions to potentially merge/cluster
            similar_question_id = self.find_similar_question(channel_id, message_text, question_analysis)
            
            if similar_question_id:
                print(f"🔗 Found similar question {similar_question_id}, updating existing question")
                self.update_clustered_question(similar_question_id, message_text, user_name, timestamp)
            else:
                # Store new question in database
                question_data = {
                    "text": message_text,
                    "user_id": user_id,
                    "user_name": user_name,
                    "channel_id": channel_id,
                    "timestamp": timestamp,
                    "message_ts": message_ts,
                    "confidence_score": question_analysis["confidence"],
                    "metadata": {
                        "question_type": question_analysis.get("question_type", "unknown"),
                        "detected_at": datetime.now().isoformat(),
                        "original_text": message_text
                    }
                }
                
                question_id = self.db_manager.store_question(question_data)
                print(f"✅ Stored new question with ID: {question_id}")
        
        # Always check if message could be an answer (even if it's also a question)
        self.check_for_answers(message_data, user_name)
    
    def check_for_answers(self, message_data: Dict, user_name: str):
        """Check if a message answers any recent questions in the channel."""
        channel_id = message_data["channel_id"]
        message_text = message_data["text"]
        message_ts = message_data["ts"]
        user_id = message_data["user_id"]
        timestamp = message_data["timestamp"]
        
        # Get ALL unanswered questions from this channel (no timeout)
        recent_questions = self.db_manager.find_recent_questions(
            channel_id, hours=None
        )
        
        if not recent_questions:
            return
        
        # Build context from message buffer
        context_messages = list(self.message_buffers[channel_id])
        context_text = "\n".join([
            f"{self.get_user_name(msg.get('user_id', ''))}: {msg.get('text', '')}"
            for msg in context_messages[-5:]  # Last 5 messages for context
        ])
        
        # Check against each recent question
        for question in recent_questions:
            answer_analysis = self.openai_analyzer.is_answer_to_question(
                question["text"], message_text, context_text
            )
            
            if answer_analysis.get("is_answer", False) and \
               answer_analysis.get("confidence", 0) >= self.config.ANSWER_DETECTION_THRESHOLD:
                
                print(f"💡 Detected answer (confidence: {answer_analysis['confidence']:.2f}) to question: {question['text'][:50]}...")
                print(f"   Answer: {message_text[:100]}...")
                
                # Store answer in database
                answer_data = {
                    "text": message_text,
                    "user_id": user_id,
                    "user_name": user_name,
                    "channel_id": channel_id,
                    "timestamp": timestamp,
                    "message_ts": message_ts,
                    "confidence_score": answer_analysis["confidence"],
                    "metadata": {
                        "answer_quality": answer_analysis.get("answer_quality", "unknown"),
                        "question_id": question["id"],
                        "detected_at": datetime.now().isoformat()
                    }
                }
                
                answer_id = self.db_manager.store_answer(answer_data, question["id"])
                print(f"✅ Stored answer with ID: {answer_id} (linked to question {question['id']})")
                
                # Also store as Q&A pair for backward compatibility
                qa_pair = {
                    "question": question["text"],
                    "answer": message_text,
                    "question_user": question["user_name"],
                    "answer_user": user_name,
                    "channel": channel_id,
                    "timestamp": timestamp.isoformat(),
                    "confidence_score": min(question["confidence_score"], answer_analysis["confidence"])
                }
                
                self.db_manager.store_qa_pair(qa_pair)
                print(f"✅ Stored Q&A pair for backward compatibility")
                
                # Continue checking other questions - one message can answer multiple questions
    
    def find_similar_question(self, channel_id: str, question_text: str, question_analysis: Dict) -> Optional[int]:
        """Find existing questions that are similar/related to this one."""
        # Get recent questions from the same channel
        existing_questions = self.db_manager.find_recent_questions(channel_id, hours=72)  # Look at last 3 days for clustering
        
        if not existing_questions:
            return None
        
        # Use OpenAI to find similar questions
        try:
            similar_question = self.openai_analyzer.find_similar_question(
                question_text, existing_questions
            )
            
            if similar_question and similar_question.get("is_similar", False):
                similarity_score = similar_question.get("similarity_score", 0)
                if similarity_score >= 0.8:  # High similarity threshold for merging
                    return similar_question["question_id"]
                    
        except Exception as e:
            print(f"❌ Error finding similar questions: {e}")
            
        return None
    
    def update_clustered_question(self, question_id: int, new_question_text: str, user_name: str, timestamp: datetime):
        """Update an existing question by clustering with a new related question."""
        try:
            # Get the existing question
            existing_question = self.db_manager.get_question_by_id(question_id)
            if not existing_question:
                return
                
            # Use OpenAI to create a generalized version that covers both questions
            generalized_question = self.openai_analyzer.generalize_questions(
                existing_question["text"], new_question_text
            )
            
            if generalized_question and generalized_question.get("generalized_text"):
                # Update the existing question with the generalized version
                updated_metadata = json.loads(existing_question.get("metadata", "{}"))
                updated_metadata["clustered_questions"] = updated_metadata.get("clustered_questions", [])
                updated_metadata["clustered_questions"].append({
                    "text": new_question_text,
                    "user": user_name,
                    "timestamp": timestamp.isoformat()
                })
                updated_metadata["last_updated"] = datetime.now().isoformat()
                
                self.db_manager.update_question(
                    question_id,
                    text=generalized_question["generalized_text"],
                    metadata=updated_metadata
                )
                print(f"🔄 Updated question {question_id} with generalized version")
                
        except Exception as e:
            print(f"❌ Error updating clustered question: {e}")
    
    def start_monitoring(self):
        """Start real-time monitoring."""
        if not self.config.REALTIME_ENABLED:
            print("⚠️  Real-time monitoring is disabled in config")
            return
        
        print("🚀 Starting real-time Q&A monitoring...")
        
        # Set up event handler
        self.socket_client.socket_mode_request_listeners.append(self.handle_message_event)
        
        # Start background processing thread
        self.running = True
        self.processing_thread = threading.Thread(target=self.process_message_queue, daemon=True)
        self.processing_thread.start()
        
        try:
            # Start Socket Mode connection
            self.socket_client.connect()
            print("✅ Connected to Slack via Socket Mode")
            print("🔍 Monitoring for new messages...")
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down real-time monitor...")
            self.stop_monitoring()
        except Exception as e:
            print(f"❌ Real-time monitoring error: {e}")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.running = False
        
        if self.socket_client:
            self.socket_client.disconnect()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        print("✅ Real-time monitoring stopped")
    
    def get_status(self) -> Dict:
        """Get current monitoring status."""
        stats = self.db_manager.get_statistics()
        
        return {
            "monitoring_active": self.running,
            "message_buffers": {k: len(v) for k, v in self.message_buffers.items()},
            "processing_queue_size": len(self.processing_queue),
            "user_cache_size": len(self.user_cache),
            "database_stats": stats
        }


def main():
    """Main entry point for real-time monitoring."""
    monitor = RealtimeQAMonitor()
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()