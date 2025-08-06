#!/usr/bin/env python
"""
OpenAI integration for Q&A pair extraction from conversations.
"""
import json
import openai
from config.config_manager import get_required_env_vars, PipelineConfig


class OpenAIAnalyzer:
    """Handles OpenAI API calls for Q&A extraction."""
    
    def __init__(self):
        env_vars = get_required_env_vars()
        openai.api_key = env_vars['OPENAI_API_KEY']
        self.config = PipelineConfig()
    
    def extract_qa_pairs_from_conversation(self, conversation_text):
        """Call OpenAI to analyze conversation for Q&A pairs."""
        try:
            response = openai.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at analyzing Slack conversations to identify question-answer pairs.

Your task:
1. Find questions that seek information (may or may not end with "?")
2. Find corresponding answers that provide helpful information
3. Consider conversational context - answers might come several messages later

Return ONLY a valid JSON array with this exact format:
[{"question": "exact question text", "answer": "exact answer text", "question_user": "user name", "answer_user": "user name"}]

If no clear Q&A pairs exist, return: []"""
                    },
                    {
                        "role": "user", 
                        "content": f"Analyze this conversation:\n\n{conversation_text}"
                    }
                ],
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=self.config.OPENAI_TEMPERATURE
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                qa_pairs = json.loads(result_text)
                return qa_pairs if isinstance(qa_pairs, list) else []
            except json.JSONDecodeError:
                print(f"⚠️  Failed to parse OpenAI JSON response: {result_text[:100]}...")
                return []
                
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return []
    
    def is_question(self, message_text: str) -> dict:
        """Analyze if a single message is a question and return confidence score."""
        try:
            response = openai.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze if this message is a question seeking information or help.

Consider:
- Direct questions (ends with "?")
- Implicit questions ("how do I...", "what is...", "can someone help...")
- Requests for information or assistance
- Troubleshooting requests

Return ONLY a JSON object:
{"is_question": true/false, "confidence": 0.0-1.0, "question_type": "direct/implicit/help_request/none"}"""
                    },
                    {
                        "role": "user",
                        "content": f"Message: {message_text}"
                    }
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {"is_question": False, "confidence": 0.0, "question_type": "none"}
                
        except Exception as e:
            print(f"❌ Question analysis error: {e}")
            return {"is_question": False, "confidence": 0.0, "question_type": "none"}
    
    def is_answer_to_question(self, question_text: str, potential_answer: str, context: str = "") -> dict:
        """Analyze if a message is an answer to a specific question."""
        try:
            context_prompt = f"\n\nContext: {context}" if context else ""
            
            response = openai.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze if the potential answer addresses the given question.

Consider:
- Direct answers that provide the requested information
- Partial answers that address part of the question
- Helpful responses that move toward a solution
- Context and conversational flow

Return ONLY a JSON object:
{"is_answer": true/false, "confidence": 0.0-1.0, "answer_quality": "direct/partial/helpful/irrelevant"}"""
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question_text}\n\nPotential Answer: {potential_answer}{context_prompt}"
                    }
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {"is_answer": False, "confidence": 0.0, "answer_quality": "irrelevant"}
                
        except Exception as e:
            print(f"❌ Answer analysis error: {e}")
            return {"is_answer": False, "confidence": 0.0, "answer_quality": "irrelevant"}