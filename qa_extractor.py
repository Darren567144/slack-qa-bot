#!/usr/bin/env python
"""
Q&A extraction orchestration and data processing.
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from core.slack_client import SlackDataFetcher
from core.message_processor import MessageProcessor
from core.openai_analyzer import OpenAIAnalyzer
from config.config_manager import PipelineConfig
from database.cloud_database_manager import CloudDatabaseManager as DatabaseManager


class QAExtractor:
    """Orchestrates the Q&A extraction process."""
    
    def __init__(self):
        self.slack_fetcher = SlackDataFetcher()
        self.message_processor = MessageProcessor()
        self.openai_analyzer = OpenAIAnalyzer()
        self.config = PipelineConfig()
        self.db_manager = DatabaseManager()
    
    def extract_qa_pairs(self, max_messages_per_channel=None):
        """Extract Q&A pairs using OpenAI analysis."""
        print("🚀 Starting Q&A extraction...")
        
        if max_messages_per_channel is None:
            max_messages_per_channel = self.config.MAX_MESSAGES_PER_CHANNEL
        
        # Setup output
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get channels (now supports autonomous access)
        channels_to_process = self.slack_fetcher.get_all_accessible_channels()
        print(f"Processing {len(channels_to_process)} channels (autonomous access enabled)")
        
        all_qa_pairs = []
        
        for i, channel_id in enumerate(channels_to_process, 1):
            print(f"🔍 Processing channel {i}/{len(channels_to_process)}: {channel_id}...")
            
            # Get recent messages
            messages = self.slack_fetcher.fetch_recent_messages(channel_id, max_messages_per_channel)
            if not messages:
                print(f"   ⚠️  No messages found, skipping...")
                continue
            
            # Get user names
            user_names = self.slack_fetcher.get_user_names_for_messages(messages)
            
            # Create conversation windows
            windows = self.message_processor.create_conversation_windows(messages, user_names)
            print(f"   📊 Created {len(windows)} conversation windows to analyze")
            
            # Process each window
            for j, window in enumerate(windows, 1):
                print(f"   🤖 Analyzing window {j}/{len(windows)} ({len(window['messages'])} messages)...")
                pairs = self.openai_analyzer.extract_qa_pairs_from_conversation(window['formatted_text'])
                
                if pairs:
                    print(f"      ✅ Found {len(pairs)} Q&A pairs")
                else:
                    print(f"      ℹ️  No Q&A pairs found in this window")
                    
                for pair in pairs:
                    pair["channel"] = channel_id
                    pair["timestamp"] = datetime.now().isoformat()
                    all_qa_pairs.append(pair)
                    
                    # Store in database
                    self.db_manager.store_qa_pair(pair)
            
            print(f"   🎯 Channel {channel_id} complete: {len([p for p in all_qa_pairs if p['channel'] == channel_id])} total Q&A pairs")
        
        # Save raw results
        raw_jsonl = self.config.OUTPUT_DIR / f"qa_raw_{today}.jsonl"
        with raw_jsonl.open("w", encoding="utf-8") as jl:
            for pair in all_qa_pairs:
                jl.write(json.dumps(pair, ensure_ascii=False) + "\n")
        
        print(f"✅ Extracted {len(all_qa_pairs)} raw Q&A pairs")
        return all_qa_pairs, raw_jsonl
    
    def deduplicate_qa_pairs(self, raw_jsonl_file):
        """Remove duplicate Q&A pairs."""
        print("🔄 Deduplicating Q&A pairs...")
        
        seen_pairs = set()
        unique_qa = []
        duplicates_removed = 0
        
        with open(raw_jsonl_file, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                
                question = data.get("question", "").strip().lower() if data.get("question") else ""
                answer = data.get("answer", "").strip().lower() if data.get("answer") else ""
                
                signature = (question, answer, data.get("channel", ""))
                
                if signature not in seen_pairs:
                    seen_pairs.add(signature)
                    unique_qa.append(data)
                else:
                    duplicates_removed += 1
        
        # Save deduplicated results
        today = datetime.now().strftime("%Y-%m-%d")
        output_jsonl = self.config.OUTPUT_DIR / f"qa_deduplicated_{today}.jsonl"
        output_csv = self.config.OUTPUT_DIR / f"qa_deduplicated_{today}.csv"
        
        with open(output_jsonl, 'w') as f:
            for qa in unique_qa:
                f.write(json.dumps(qa, ensure_ascii=False) + '\n')
        
        with open(output_csv, 'w', newline='') as f:
            if unique_qa:
                fieldnames = ["question", "answer", "question_user", "answer_user", "channel", "timestamp"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(unique_qa)
        
        print(f"✅ Deduplication complete:")
        print(f"   Original: {len(unique_qa) + duplicates_removed} Q&A pairs")
        print(f"   Unique: {len(unique_qa)} Q&A pairs")
        print(f"   Removed: {duplicates_removed} duplicates")
        
        return unique_qa, output_jsonl