#!/usr/bin/env python
"""
OpenAI integration for Q&A pair extraction from conversations.
"""
import json
from openai import OpenAI
from config.config_manager import get_required_env_vars, PipelineConfig


class OpenAIAnalyzer:
    """Handles OpenAI API calls for Q&A extraction."""
    
    def __init__(self):
        env_vars = get_required_env_vars()
        self.client = OpenAI(api_key=env_vars['OPENAI_API_KEY'])
        self.config = PipelineConfig()
    
    def extract_qa_pairs_from_conversation(self, conversation_text):
        """Call OpenAI to analyze conversation for Q&A pairs."""
        try:
            response = self.client.chat.completions.create(
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
                max_completion_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=0.1
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
            response = self.client.chat.completions.create(
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
                max_completion_tokens=100,
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
            
            response = self.client.chat.completions.create(
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
                max_completion_tokens=100,
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
    
    def find_similar_question(self, new_question: str, existing_questions: list) -> dict:
        """Find if a new question is similar to any existing questions."""
        try:
            questions_text = "\n".join([
                f"ID: {q['id']} - {q['text']}" for q in existing_questions[:10]  # Limit to avoid token overflow
            ])
            
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze if the new question is similar to any existing questions.
Look for:
- Same topic/subject matter
- Follow-up questions to the same issue
- Rephrased versions of the same question
- Related questions that could be clustered together

Return ONLY a JSON object:
{"is_similar": true/false, "similarity_score": 0.0-1.0, "question_id": id_number_or_null, "reason": "explanation"}

Use high similarity threshold (0.8+) for true matches."""
                    },
                    {
                        "role": "user",
                        "content": f"New Question: {new_question}\n\nExisting Questions:\n{questions_text}"
                    }
                ],
                max_completion_tokens=200,
                temperature=0.2
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
                return {"is_similar": False, "similarity_score": 0.0, "question_id": None}
                
        except Exception as e:
            print(f"❌ Similar question analysis error: {e}")
            return {"is_similar": False, "similarity_score": 0.0, "question_id": None}
    
    def generalize_questions(self, original_question: str, new_question: str) -> dict:
        """Create a generalized version that covers both related questions."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Create a generalized question that covers both the original and new question.
The generalized version should:
- Capture the core intent of both questions
- Be more broadly applicable
- Remove specific details that make it too narrow
- Maintain the essential information need

Return ONLY a JSON object:
{"generalized_text": "generalized question", "covers_both": true/false, "explanation": "why this works"}"""
                    },
                    {
                        "role": "user",
                        "content": f"Original Question: {original_question}\n\nNew Related Question: {new_question}"
                    }
                ],
                max_completion_tokens=200,
                temperature=0.2
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
                return {"generalized_text": original_question, "covers_both": False}
                
        except Exception as e:
            print(f"❌ Question generalization error: {e}")
            return {"generalized_text": original_question, "covers_both": False}