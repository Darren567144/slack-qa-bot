#!/usr/bin/env python
"""
Database management for Q&A storage and retrieval.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from config.config_manager import PipelineConfig


class DatabaseManager:
    """Handles SQLite database operations for Q&A storage."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = PipelineConfig()
        if db_path is None:
            db_path = self.config.OUTPUT_DIR / "qa_database.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Questions table
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    user_id TEXT,
                    user_name TEXT,
                    channel_id TEXT,
                    timestamp DATETIME,
                    message_ts TEXT UNIQUE,
                    confidence_score REAL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Answers table
                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER,
                    text TEXT NOT NULL,
                    user_id TEXT,
                    user_name TEXT,
                    channel_id TEXT,
                    timestamp DATETIME,
                    message_ts TEXT UNIQUE,
                    confidence_score REAL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions (id)
                );
                
                -- Q&A pairs table (for backward compatibility with existing extraction)
                CREATE TABLE IF NOT EXISTS qa_pairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    question_user TEXT,
                    answer_user TEXT,
                    channel TEXT,
                    timestamp DATETIME,
                    confidence_score REAL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(question, answer, channel)
                );
                
                -- Processed messages table (to avoid reprocessing)
                CREATE TABLE IF NOT EXISTS processed_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_ts TEXT UNIQUE,
                    channel_id TEXT,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_questions_channel ON questions(channel_id);
                CREATE INDEX IF NOT EXISTS idx_questions_timestamp ON questions(timestamp);
                CREATE INDEX IF NOT EXISTS idx_answers_question_id ON answers(question_id);
                CREATE INDEX IF NOT EXISTS idx_answers_channel ON answers(channel_id);
                CREATE INDEX IF NOT EXISTS idx_qa_pairs_channel ON qa_pairs(channel);
                CREATE INDEX IF NOT EXISTS idx_processed_messages_ts ON processed_messages(message_ts);
            """)
        print(f"✅ Database initialized at {self.db_path}")
    
    def store_qa_pair(self, qa_data: Dict) -> int:
        """Store a Q&A pair (backward compatibility with existing system)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO qa_pairs 
                (question, answer, question_user, answer_user, channel, timestamp, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                qa_data.get('question', ''),
                qa_data.get('answer', ''),
                qa_data.get('question_user', ''),
                qa_data.get('answer_user', ''),
                qa_data.get('channel', ''),
                qa_data.get('timestamp'),
                qa_data.get('confidence_score', 0.0),
                json.dumps(qa_data.get('metadata', {}))
            ))
            return cursor.lastrowid
    
    def store_question(self, question_data: Dict) -> int:
        """Store a question and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO questions 
                (text, user_id, user_name, channel_id, timestamp, message_ts, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question_data.get('text', ''),
                question_data.get('user_id', ''),
                question_data.get('user_name', ''),
                question_data.get('channel_id', ''),
                question_data.get('timestamp').isoformat() if isinstance(question_data.get('timestamp'), datetime) else question_data.get('timestamp'),
                question_data.get('message_ts', ''),
                question_data.get('confidence_score', 0.0),
                json.dumps(question_data.get('metadata', {}))
            ))
            return cursor.lastrowid
    
    def store_answer(self, answer_data: Dict, question_id: Optional[int] = None) -> int:
        """Store an answer, optionally linking it to a question."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO answers 
                (question_id, text, user_id, user_name, channel_id, timestamp, message_ts, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question_id,
                answer_data.get('text', ''),
                answer_data.get('user_id', ''),
                answer_data.get('user_name', ''),
                answer_data.get('channel_id', ''),
                answer_data.get('timestamp').isoformat() if isinstance(answer_data.get('timestamp'), datetime) else answer_data.get('timestamp'),
                answer_data.get('message_ts', ''),
                answer_data.get('confidence_score', 0.0),
                json.dumps(answer_data.get('metadata', {}))
            ))
            return cursor.lastrowid
    
    def find_recent_questions(self, channel_id: str, hours: int = 24) -> List[Dict]:
        """Find recent unanswered questions in a channel."""
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.id, q.text, q.user_id, q.user_name, q.timestamp, q.message_ts, q.confidence_score
                FROM questions q
                LEFT JOIN answers a ON q.id = a.question_id
                WHERE q.channel_id = ? 
                  AND q.timestamp > ?
                  AND a.id IS NULL
                ORDER BY q.timestamp DESC
            """, (channel_id, cutoff_time))
            
            questions = []
            for row in cursor.fetchall():
                questions.append({
                    'id': row[0],
                    'text': row[1],
                    'user_id': row[2],
                    'user_name': row[3],
                    'timestamp': row[4],
                    'message_ts': row[5],
                    'confidence_score': row[6]
                })
            return questions
    
    def is_message_processed(self, message_ts: str) -> bool:
        """Check if a message has already been processed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM processed_messages WHERE message_ts = ?", (message_ts,))
            return cursor.fetchone() is not None
    
    def mark_message_processed(self, message_ts: str, channel_id: str):
        """Mark a message as processed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO processed_messages (message_ts, channel_id)
                VALUES (?, ?)
            """, (message_ts, channel_id))
    
    def get_qa_pairs(self, channel: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve Q&A pairs from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if channel:
                cursor.execute("""
                    SELECT question, answer, question_user, answer_user, channel, timestamp, confidence_score
                    FROM qa_pairs WHERE channel = ? ORDER BY created_at DESC LIMIT ?
                """, (channel, limit))
            else:
                cursor.execute("""
                    SELECT question, answer, question_user, answer_user, channel, timestamp, confidence_score
                    FROM qa_pairs ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            
            pairs = []
            for row in cursor.fetchall():
                pairs.append({
                    'question': row[0],
                    'answer': row[1],
                    'question_user': row[2],
                    'answer_user': row[3],
                    'channel': row[4],
                    'timestamp': row[5],
                    'confidence_score': row[6]
                })
            return pairs
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count records in each table
            cursor.execute("SELECT COUNT(*) FROM questions")
            questions_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM answers")
            answers_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM qa_pairs")
            qa_pairs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM processed_messages")
            processed_count = cursor.fetchone()[0]
            
            # Get unique channels
            cursor.execute("SELECT COUNT(DISTINCT channel_id) FROM questions")
            unique_channels = cursor.fetchone()[0]
            
            return {
                'questions': questions_count,
                'answers': answers_count,
                'qa_pairs': qa_pairs_count,
                'processed_messages': processed_count,
                'unique_channels': unique_channels,
                'database_path': str(self.db_path)
            }
    
    def export_to_csv(self, output_file: str, table: str = 'qa_pairs'):
        """Export data to CSV (backward compatibility)."""
        import csv
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if table == 'qa_pairs':
                cursor.execute("""
                    SELECT question, answer, question_user, answer_user, channel, timestamp
                    FROM qa_pairs ORDER BY created_at
                """)
                fieldnames = ['question', 'answer', 'question_user', 'answer_user', 'channel', 'timestamp']
            elif table == 'questions':
                cursor.execute("""
                    SELECT text, user_name, channel_id, timestamp, confidence_score
                    FROM questions ORDER BY timestamp
                """)
                fieldnames = ['text', 'user_name', 'channel_id', 'timestamp', 'confidence_score']
            else:
                raise ValueError(f"Unknown table: {table}")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                writer.writerows(cursor.fetchall())
        
        print(f"✅ Exported {table} to {output_file}")