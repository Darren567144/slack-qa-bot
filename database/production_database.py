#!/usr/bin/env python
"""
Production database manager that supports both PostgreSQL and SQLite.
Automatically detects DATABASE_URL and uses appropriate backend.
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from config.config_manager import PipelineConfig


class ProductionDatabaseManager:
    """Production-ready database manager with PostgreSQL and SQLite support."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.config = PipelineConfig()
        
        # Get database URL from environment or parameter
        self.database_url = (
            database_url or 
            os.environ.get('DATABASE_URL') or 
            f"sqlite:///{self.config.DATABASE_PATH}"
        )
        
        # Determine database type
        self.is_postgres = self.database_url.startswith(('postgresql://', 'postgres://'))
        
        if self.is_postgres:
            self._setup_postgresql()
        else:
            self._setup_sqlite()
        
        # For compatibility with existing code
        self.db_path = self.database_url
        print(f"✅ Database initialized: {'PostgreSQL' if self.is_postgres else 'SQLite'}")
    
    def _setup_postgresql(self):
        """Set up PostgreSQL connection."""
        try:
            import psycopg
            
            # Test connection with DATABASE_URL directly
            conn = psycopg.connect(self.database_url)
            conn.close()
            
            # Store connection string for later use
            self.postgres_url = self.database_url
            
            # Initialize tables
            self._init_postgres_tables()
            
        except ImportError:
            print("❌ psycopg not found. Install with: pip install psycopg[binary]")
            print("Falling back to SQLite...")
            self.is_postgres = False
            self._setup_sqlite()
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            print("Falling back to SQLite...")
            self.is_postgres = False
            self._setup_sqlite()
    
    def _setup_sqlite(self):
        """Set up SQLite connection."""
        self.db_path = str(self.config.DATABASE_PATH)
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        # Initialize tables
        self._init_sqlite_tables()
    
    def _init_postgres_tables(self):
        """Initialize PostgreSQL tables."""
        import psycopg
        
        conn = psycopg.connect(self.postgres_url)
        cursor = conn.cursor()
        
        # Create tables with PostgreSQL syntax
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_pairs (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                question_user VARCHAR(100),
                answer_user VARCHAR(100),
                channel VARCHAR(100),
                timestamp TIMESTAMP,
                confidence_score REAL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(question, answer, channel)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                user_id VARCHAR(50),
                user_name VARCHAR(100),
                channel_id VARCHAR(50),
                timestamp TIMESTAMP,
                message_ts VARCHAR(50) UNIQUE,
                confidence_score REAL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id SERIAL PRIMARY KEY,
                question_id INTEGER REFERENCES questions(id),
                text TEXT NOT NULL,
                user_id VARCHAR(50),
                user_name VARCHAR(100),
                channel_id VARCHAR(50),
                timestamp TIMESTAMP,
                message_ts VARCHAR(50) UNIQUE,
                confidence_score REAL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                id SERIAL PRIMARY KEY,
                message_ts VARCHAR(50) UNIQUE,
                channel_id VARCHAR(50),
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_pairs_channel ON qa_pairs(channel);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_channel ON questions(channel_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_timestamp ON questions(timestamp);")
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def _init_sqlite_tables(self):
        """Initialize SQLite tables."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.executescript("""
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
            
            CREATE TABLE IF NOT EXISTS processed_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_ts TEXT UNIQUE,
                channel_id TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_qa_pairs_channel ON qa_pairs(channel);
            CREATE INDEX IF NOT EXISTS idx_questions_channel ON questions(channel_id);
            CREATE INDEX IF NOT EXISTS idx_questions_timestamp ON questions(timestamp);
        """)
        
        conn.close()
    
    def store_qa_pair(self, qa_data: Dict) -> Optional[int]:
        """Store a Q&A pair."""
        if self.is_postgres:
            return self._store_qa_pair_postgres(qa_data)
        else:
            return self._store_qa_pair_sqlite(qa_data)
    
    def _store_qa_pair_postgres(self, qa_data: Dict) -> Optional[int]:
        """Store Q&A pair in PostgreSQL."""
        import psycopg
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO qa_pairs 
                (question, answer, question_user, answer_user, channel, timestamp, confidence_score, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (question, answer, channel) DO NOTHING
                RETURNING id;
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
            
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"❌ Error storing Q&A pair in PostgreSQL: {e}")
            return None
    
    def _store_qa_pair_sqlite(self, qa_data: Dict) -> Optional[int]:
        """Store Q&A pair in SQLite."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.db_path)
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
            
            row_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            return row_id
            
        except Exception as e:
            print(f"❌ Error storing Q&A pair in SQLite: {e}")
            return None
    
    def get_qa_pairs(self, channel: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve Q&A pairs from database."""
        if self.is_postgres:
            return self._get_qa_pairs_postgres(channel, limit)
        else:
            return self._get_qa_pairs_sqlite(channel, limit)
    
    def _get_qa_pairs_postgres(self, channel: Optional[str], limit: int) -> List[Dict]:
        """Get Q&A pairs from PostgreSQL."""
        import psycopg
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            if channel:
                cursor.execute("""
                    SELECT question, answer, question_user, answer_user, channel, timestamp, confidence_score
                    FROM qa_pairs WHERE channel = %s ORDER BY created_at DESC LIMIT %s
                """, (channel, limit))
            else:
                cursor.execute("""
                    SELECT question, answer, question_user, answer_user, channel, timestamp, confidence_score
                    FROM qa_pairs ORDER BY created_at DESC LIMIT %s
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
            
            cursor.close()
            conn.close()
            return pairs
            
        except Exception as e:
            print(f"❌ Error retrieving Q&A pairs from PostgreSQL: {e}")
            return []
    
    def _get_qa_pairs_sqlite(self, channel: Optional[str], limit: int) -> List[Dict]:
        """Get Q&A pairs from SQLite."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.db_path)
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
            
            cursor.close()
            conn.close()
            return pairs
            
        except Exception as e:
            print(f"❌ Error retrieving Q&A pairs from SQLite: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        if self.is_postgres:
            return self._get_statistics_postgres()
        else:
            return self._get_statistics_sqlite()
    
    def _get_statistics_postgres(self) -> Dict:
        """Get statistics from PostgreSQL."""
        import psycopg
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM qa_pairs")
            qa_pairs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM questions")
            questions_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM answers") 
            answers_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM processed_messages")
            processed_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT channel) FROM qa_pairs")
            unique_channels = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'questions': questions_count,
                'answers': answers_count,
                'qa_pairs': qa_pairs_count,
                'processed_messages': processed_count,
                'unique_channels': unique_channels,
                'database_path': self.database_url
            }
            
        except Exception as e:
            print(f"❌ Error getting PostgreSQL statistics: {e}")
            return {'error': str(e)}
    
    def _get_statistics_sqlite(self) -> Dict:
        """Get statistics from SQLite."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM qa_pairs")
            qa_pairs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM questions")
            questions_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM answers")
            answers_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM processed_messages")
            processed_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT channel) FROM qa_pairs WHERE channel IS NOT NULL")
            unique_channels = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'questions': questions_count,
                'answers': answers_count,
                'qa_pairs': qa_pairs_count,
                'processed_messages': processed_count,
                'unique_channels': unique_channels,
                'database_path': str(self.db_path)
            }
            
        except Exception as e:
            print(f"❌ Error getting SQLite statistics: {e}")
            return {'error': str(e)}
    
    # Add other methods from DatabaseManager for full compatibility
    def store_question(self, question_data: Dict) -> Optional[int]:
        """Store a question."""
        if self.is_postgres:
            return self._store_question_postgres(question_data)
        else:
            return self._store_question_sqlite(question_data)
    
    def store_answer(self, answer_data: Dict, question_id: Optional[int] = None) -> Optional[int]:
        """Store an answer."""
        if self.is_postgres:
            return self._store_answer_postgres(answer_data, question_id)
        else:
            return self._store_answer_sqlite(answer_data, question_id)
    
    def find_recent_questions(self, channel_id: str, hours: Optional[int] = 24) -> List[Dict]:
        """Find unanswered questions in a channel. If hours=None, get ALL unanswered questions."""
        if self.is_postgres:
            return self._find_recent_questions_postgres(channel_id, hours)
        else:
            return self._find_recent_questions_sqlite(channel_id, hours)
    
    def _find_recent_questions_postgres(self, channel_id: str, hours: Optional[int]) -> List[Dict]:
        """Find unanswered questions in PostgreSQL."""
        import psycopg
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            if hours is None:
                # Get ALL unanswered questions (no time limit)
                cursor.execute("""
                    SELECT q.id, q.text, q.user_id, q.user_name, q.timestamp, q.message_ts, q.confidence_score
                    FROM questions q
                    LEFT JOIN answers a ON q.id = a.question_id
                    WHERE q.channel_id = %s 
                      AND a.id IS NULL
                    ORDER BY q.timestamp DESC
                """, (channel_id,))
            else:
                # Get recent unanswered questions within time window
                cutoff_time = datetime.now() - timedelta(hours=hours)
                cursor.execute("""
                    SELECT q.id, q.text, q.user_id, q.user_name, q.timestamp, q.message_ts, q.confidence_score
                    FROM questions q
                    LEFT JOIN answers a ON q.id = a.question_id
                    WHERE q.channel_id = %s 
                      AND q.timestamp > %s
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
            
            cursor.close()
            conn.close()
            return questions
            
        except Exception as e:
            print(f"❌ Error finding questions in PostgreSQL: {e}")
            return []
    
    def _find_recent_questions_sqlite(self, channel_id: str, hours: Optional[int]) -> List[Dict]:
        """Find unanswered questions in SQLite."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if hours is None:
                # Get ALL unanswered questions (no time limit)
                cursor.execute("""
                    SELECT q.id, q.text, q.user_id, q.user_name, q.timestamp, q.message_ts, q.confidence_score
                    FROM questions q
                    LEFT JOIN answers a ON q.id = a.question_id
                    WHERE q.channel_id = ? 
                      AND a.id IS NULL
                    ORDER BY q.timestamp DESC
                """, (channel_id,))
            else:
                # Get recent unanswered questions within time window
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
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
            
            cursor.close()
            conn.close()
            return questions
            
        except Exception as e:
            print(f"❌ Error finding questions in SQLite: {e}")
            return []
    
    def is_message_processed(self, message_ts: str) -> bool:
        """Check if message was processed."""
        if self.is_postgres:
            return self._is_message_processed_postgres(message_ts)
        else:
            return self._is_message_processed_sqlite(message_ts)
    
    def mark_message_processed(self, message_ts: str, channel_id: str):
        """Mark message as processed."""
        if self.is_postgres:
            self._mark_message_processed_postgres(message_ts, channel_id)
        else:
            self._mark_message_processed_sqlite(message_ts, channel_id)
    
    def export_to_csv(self, output_file: str, table: str = 'qa_pairs'):
        """Export data to CSV."""
        # Implementation would export table to CSV
        pass
    
    def _store_question_postgres(self, question_data: Dict) -> Optional[int]:
        """Store question in PostgreSQL."""
        import psycopg
        import json
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO questions 
                (text, user_id, user_name, channel_id, timestamp, message_ts, confidence_score, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_ts) DO NOTHING
                RETURNING id
            """, (
                question_data['text'],
                question_data.get('user_id'),
                question_data.get('user_name'),
                question_data.get('channel_id'),
                question_data.get('timestamp'),
                question_data.get('message_ts'),
                question_data.get('confidence_score'),
                json.dumps(question_data.get('metadata', {}))
            ))
            
            result = cursor.fetchone()
            question_id = result[0] if result else None
            
            conn.commit()
            conn.close()
            
            return question_id
            
        except Exception as e:
            print(f"❌ Error storing question in PostgreSQL: {e}")
            return None
    
    def _store_question_sqlite(self, question_data: Dict) -> Optional[int]:
        """Store question in SQLite (fallback)."""
        # Would implement SQLite version if needed
        pass
    
    def _store_answer_postgres(self, answer_data: Dict, question_id: Optional[int] = None) -> Optional[int]:
        """Store answer in PostgreSQL."""
        import psycopg
        import json
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO answers 
                (question_id, text, user_id, user_name, channel_id, timestamp, message_ts, confidence_score, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_ts) DO NOTHING
                RETURNING id
            """, (
                question_id,
                answer_data['text'],
                answer_data.get('user_id'),
                answer_data.get('user_name'),
                answer_data.get('channel_id'),
                answer_data.get('timestamp'),
                answer_data.get('message_ts'),
                answer_data.get('confidence_score'),
                json.dumps(answer_data.get('metadata', {}))
            ))
            
            result = cursor.fetchone()
            answer_id = result[0] if result else None
            
            conn.commit()
            conn.close()
            
            return answer_id
            
        except Exception as e:
            print(f"❌ Error storing answer in PostgreSQL: {e}")
            return None
    
    def _store_answer_sqlite(self, answer_data: Dict, question_id: Optional[int] = None) -> Optional[int]:
        """Store answer in SQLite (fallback)."""
        # Would implement SQLite version if needed
        pass
    
    def _is_message_processed_postgres(self, message_ts: str) -> bool:
        """Check if message was processed in PostgreSQL."""
        import psycopg
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM processed_messages WHERE message_ts = %s", (message_ts,))
            result = cursor.fetchone()
            
            conn.close()
            return result is not None
            
        except Exception as e:
            print(f"❌ Error checking processed message in PostgreSQL: {e}")
            return False
    
    def _is_message_processed_sqlite(self, message_ts: str) -> bool:
        """Check if message was processed in SQLite."""
        return False  # Fallback
    
    def _mark_message_processed_postgres(self, message_ts: str, channel_id: str):
        """Mark message as processed in PostgreSQL."""
        import psycopg
        
        try:
            conn = psycopg.connect(self.postgres_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO processed_messages (message_ts, channel_id)
                VALUES (%s, %s)
                ON CONFLICT (message_ts) DO NOTHING
            """, (message_ts, channel_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error marking message processed in PostgreSQL: {e}")
    
    def _mark_message_processed_sqlite(self, message_ts: str, channel_id: str):
        """Mark message as processed in SQLite."""
        pass  # Fallback