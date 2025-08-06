#!/usr/bin/env python
"""
Cloud database management with PostgreSQL support for Q&A storage and retrieval.
Designed for production deployment with centralized, persistent storage.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from urllib.parse import urlparse

# SQLAlchemy imports
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from config.config_manager import PipelineConfig

# Set up logging
logger = logging.getLogger(__name__)

Base = declarative_base()


class Question(Base):
    """Question model for SQLAlchemy."""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    user_id = Column(String(50))
    user_name = Column(String(100))
    channel_id = Column(String(50))
    timestamp = Column(DateTime)
    message_ts = Column(String(50), unique=True)
    confidence_score = Column(Float)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to answers
    answers = relationship("Answer", back_populates="question")
    
    # Indexes
    __table_args__ = (
        Index('idx_questions_channel', 'channel_id'),
        Index('idx_questions_timestamp', 'timestamp'),
        Index('idx_questions_message_ts', 'message_ts'),
    )


class Answer(Base):
    """Answer model for SQLAlchemy."""
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    text = Column(Text, nullable=False)
    user_id = Column(String(50))
    user_name = Column(String(100))
    channel_id = Column(String(50))
    timestamp = Column(DateTime)
    message_ts = Column(String(50), unique=True)
    confidence_score = Column(Float)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to question
    question = relationship("Question", back_populates="answers")
    
    # Indexes
    __table_args__ = (
        Index('idx_answers_question_id', 'question_id'),
        Index('idx_answers_channel', 'channel_id'),
        Index('idx_answers_message_ts', 'message_ts'),
    )


class QAPair(Base):
    """Q&A Pair model for backward compatibility."""
    __tablename__ = 'qa_pairs'
    
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    question_user = Column(String(100))
    answer_user = Column(String(100))
    channel = Column(String(50))
    timestamp = Column(DateTime)
    confidence_score = Column(Float)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_qa_pairs_channel', 'channel'),
        Index('idx_qa_pairs_timestamp', 'timestamp'),
    )


class ProcessedMessage(Base):
    """Processed message tracking."""
    __tablename__ = 'processed_messages'
    
    id = Column(Integer, primary_key=True)
    message_ts = Column(String(50), unique=True)
    channel_id = Column(String(50))
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_processed_messages_ts', 'message_ts'),
        Index('idx_processed_messages_channel', 'channel_id'),
    )


class CloudDatabaseManager:
    """Cloud database manager with PostgreSQL support."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.config = PipelineConfig()
        
        # Get database URL from environment or parameter
        self.database_url = (
            database_url or 
            os.environ.get('DATABASE_URL') or 
            self.config.DATABASE_PATH
        )
        
        # Determine database type
        self.is_postgres = self.database_url.startswith(('postgresql://', 'postgres://'))
        
        if self.is_postgres:
            # PostgreSQL setup
            self._setup_postgresql()
        else:
            # Fallback to SQLite for local development
            self._setup_sqlite()
    
    def _setup_postgresql(self):
        """Set up PostgreSQL connection."""
        logger.info("🐘 Setting up PostgreSQL connection")
        
        # Handle Heroku/Railway DATABASE_URL format
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info("✅ PostgreSQL database initialized")
    
    def _setup_sqlite(self):
        """Fallback SQLite setup for local development."""
        logger.info("📁 Falling back to SQLite for local development")
        
        # Ensure it's a file path
        if not self.database_url.startswith('sqlite://'):
            db_path = Path(self.database_url)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.database_url = f"sqlite:///{db_path}"
        
        # Create engine
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info(f"✅ SQLite database initialized at {self.database_url}")
    
    def get_session(self) -> Session:
        """Get database session with proper error handling."""
        return self.SessionLocal()
    
    def store_qa_pair(self, qa_data: Dict) -> Optional[int]:
        """Store a Q&A pair (backward compatibility)."""
        session = self.get_session()
        try:
            qa_pair = QAPair(
                question=qa_data.get('question', ''),
                answer=qa_data.get('answer', ''),
                question_user=qa_data.get('question_user', ''),
                answer_user=qa_data.get('answer_user', ''),
                channel=qa_data.get('channel', ''),
                timestamp=self._parse_timestamp(qa_data.get('timestamp')),
                confidence_score=qa_data.get('confidence_score', 0.0),
                metadata=qa_data.get('metadata', {})
            )
            
            session.add(qa_pair)
            session.commit()
            
            qa_id = qa_pair.id
            logger.debug(f"Stored Q&A pair with ID: {qa_id}")
            return qa_id
            
        except IntegrityError:
            session.rollback()
            logger.warning("Duplicate Q&A pair, skipping")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing Q&A pair: {e}")
            return None
        finally:
            session.close()
    
    def store_question(self, question_data: Dict) -> Optional[int]:
        """Store a question and return its ID."""
        session = self.get_session()
        try:
            question = Question(
                text=question_data.get('text', ''),
                user_id=question_data.get('user_id', ''),
                user_name=question_data.get('user_name', ''),
                channel_id=question_data.get('channel_id', ''),
                timestamp=self._parse_timestamp(question_data.get('timestamp')),
                message_ts=question_data.get('message_ts', ''),
                confidence_score=question_data.get('confidence_score', 0.0),
                metadata=question_data.get('metadata', {})
            )
            
            session.add(question)
            session.commit()
            
            question_id = question.id
            logger.debug(f"Stored question with ID: {question_id}")
            return question_id
            
        except IntegrityError:
            session.rollback()
            # Try to get existing question by message_ts
            existing = session.query(Question).filter_by(
                message_ts=question_data.get('message_ts', '')
            ).first()
            if existing:
                return existing.id
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing question: {e}")
            return None
        finally:
            session.close()
    
    def store_answer(self, answer_data: Dict, question_id: Optional[int] = None) -> Optional[int]:
        """Store an answer, optionally linking it to a question."""
        session = self.get_session()
        try:
            answer = Answer(
                question_id=question_id,
                text=answer_data.get('text', ''),
                user_id=answer_data.get('user_id', ''),
                user_name=answer_data.get('user_name', ''),
                channel_id=answer_data.get('channel_id', ''),
                timestamp=self._parse_timestamp(answer_data.get('timestamp')),
                message_ts=answer_data.get('message_ts', ''),
                confidence_score=answer_data.get('confidence_score', 0.0),
                metadata=answer_data.get('metadata', {})
            )
            
            session.add(answer)
            session.commit()
            
            answer_id = answer.id
            logger.debug(f"Stored answer with ID: {answer_id}")
            return answer_id
            
        except IntegrityError:
            session.rollback()
            existing = session.query(Answer).filter_by(
                message_ts=answer_data.get('message_ts', '')
            ).first()
            if existing:
                return existing.id
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing answer: {e}")
            return None
        finally:
            session.close()
    
    def find_recent_questions(self, channel_id: str, hours: int = 24) -> List[Dict]:
        """Find recent unanswered questions in a channel."""
        session = self.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Query unanswered questions
            questions = session.query(Question).outerjoin(Answer).filter(
                Question.channel_id == channel_id,
                Question.timestamp > cutoff_time,
                Answer.id.is_(None)  # No answers
            ).order_by(Question.timestamp.desc()).all()
            
            result = []
            for q in questions:
                result.append({
                    'id': q.id,
                    'text': q.text,
                    'user_id': q.user_id,
                    'user_name': q.user_name,
                    'timestamp': q.timestamp,
                    'message_ts': q.message_ts,
                    'confidence_score': q.confidence_score
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding recent questions: {e}")
            return []
        finally:
            session.close()
    
    def is_message_processed(self, message_ts: str) -> bool:
        """Check if a message has already been processed."""
        session = self.get_session()
        try:
            exists = session.query(ProcessedMessage).filter_by(message_ts=message_ts).first()
            return exists is not None
        except Exception as e:
            logger.error(f"Error checking processed message: {e}")
            return False
        finally:
            session.close()
    
    def mark_message_processed(self, message_ts: str, channel_id: str):
        """Mark a message as processed."""
        session = self.get_session()
        try:
            processed_msg = ProcessedMessage(
                message_ts=message_ts,
                channel_id=channel_id
            )
            session.add(processed_msg)
            session.commit()
        except IntegrityError:
            session.rollback()  # Already processed, ignore
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking message processed: {e}")
        finally:
            session.close()
    
    def get_qa_pairs(self, channel: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve Q&A pairs from database."""
        session = self.get_session()
        try:
            query = session.query(QAPair)
            
            if channel:
                query = query.filter(QAPair.channel == channel)
            
            qa_pairs = query.order_by(QAPair.created_at.desc()).limit(limit).all()
            
            result = []
            for pair in qa_pairs:
                result.append({
                    'question': pair.question,
                    'answer': pair.answer,
                    'question_user': pair.question_user,
                    'answer_user': pair.answer_user,
                    'channel': pair.channel,
                    'timestamp': pair.timestamp,
                    'confidence_score': pair.confidence_score
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving Q&A pairs: {e}")
            return []
        finally:
            session.close()
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        session = self.get_session()
        try:
            questions_count = session.query(Question).count()
            answers_count = session.query(Answer).count()
            qa_pairs_count = session.query(QAPair).count()
            processed_count = session.query(ProcessedMessage).count()
            
            unique_channels = session.query(Question.channel_id).distinct().count()
            
            return {
                'questions': questions_count,
                'answers': answers_count,
                'qa_pairs': qa_pairs_count,
                'processed_messages': processed_count,
                'unique_channels': unique_channels,
                'database_url': self._sanitize_url(self.database_url),
                'database_type': 'PostgreSQL' if self.is_postgres else 'SQLite'
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
        finally:
            session.close()
    
    def export_to_csv(self, output_file: str, table: str = 'qa_pairs'):
        """Export data to CSV."""
        import csv
        
        session = self.get_session()
        try:
            if table == 'qa_pairs':
                data = session.query(
                    QAPair.question,
                    QAPair.answer,
                    QAPair.question_user,
                    QAPair.answer_user,
                    QAPair.channel,
                    QAPair.timestamp
                ).order_by(QAPair.created_at).all()
                
                fieldnames = ['question', 'answer', 'question_user', 'answer_user', 'channel', 'timestamp']
                
            elif table == 'questions':
                data = session.query(
                    Question.text,
                    Question.user_name,
                    Question.channel_id,
                    Question.timestamp,
                    Question.confidence_score
                ).order_by(Question.timestamp).all()
                
                fieldnames = ['text', 'user_name', 'channel_id', 'timestamp', 'confidence_score']
            
            else:
                raise ValueError(f"Unknown table: {table}")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                writer.writerows(data)
            
            logger.info(f"✅ Exported {table} to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
        finally:
            session.close()
    
    def health_check(self) -> Dict:
        """Check database health and connectivity."""
        try:
            session = self.get_session()
            session.execute("SELECT 1")
            session.close()
            
            return {
                'status': 'healthy',
                'database_type': 'PostgreSQL' if self.is_postgres else 'SQLite',
                'url': self._sanitize_url(self.database_url),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _parse_timestamp(self, timestamp: Union[str, datetime, None]) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if timestamp is None:
            return None
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return None
        return None
    
    def _sanitize_url(self, url: str) -> str:
        """Remove sensitive info from database URL for logging."""
        try:
            parsed = urlparse(url)
            if parsed.password:
                return url.replace(parsed.password, '***')
            return url
        except:
            return "***"
    
    def close(self):
        """Close database connections."""
        if hasattr(self, 'engine'):
            self.engine.dispose()


# Backward compatibility alias
DatabaseManager = CloudDatabaseManager