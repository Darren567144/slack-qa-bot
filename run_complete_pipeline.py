#!/usr/bin/env python
"""
Complete Slack Q&A extraction pipeline.
Runs the full workflow: Extract → Deduplicate → Generate FAQ
"""
import os, csv, json, re, time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
import openai

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        # Remove quotes and inline comments
                        value = value.split('#')[0].strip()
                        value = value.strip('"').strip("'")
                        if key and value:
                            os.environ[key] = value

def setup_clients():
    """Initialize Slack and OpenAI clients."""
    load_env()
    
    TOKEN = os.environ["SLACK_BOT_TOKEN"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    
    slack_client = WebClient(token=TOKEN)
    openai.api_key = OPENAI_API_KEY
    
    return slack_client, TOKEN

def get_member_channels(client):
    """Get channels bot is member of."""
    channels = []
    try:
        resp = client.conversations_list(types="private_channel", limit=1000)
        member_channels = [ch["id"] for ch in resp["channels"] if ch.get("is_member", False)]
        channels.extend(member_channels)
        print(f"Found {len(member_channels)} private channels (bot is member)")
    except SlackApiError as e:
        print(f"Failed to get channels: {e}")
    return channels

def get_user_name(client, user_id):
    """Get user display name for context."""
    try:
        resp = client.users_info(user=user_id)
        return resp["user"]["real_name"] or resp["user"]["name"]
    except:
        return f"User{user_id[-4:]}"

def format_message_for_llm(msg, user_names):
    """Format message with user context for LLM."""
    user_id = msg.get("user", "unknown")
    user_name = user_names.get(user_id, f"User{user_id[-4:] if user_id != 'unknown' else 'Unknown'}")
    text = msg.get("text", "").strip()
    timestamp = datetime.fromtimestamp(float(msg["ts"])).strftime("%H:%M")
    
    return f"[{timestamp}] {user_name}: {text}"

def call_openai_for_qa_extraction(conversation_text):
    """Call OpenAI to analyze conversation for Q&A pairs."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Note: o3 model not available via OpenAI API yet
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at analyzing Slack conversations to identify question-answer pairs.

Your task:
1. Find questions that seek information (may or may not end with "?")
2. Find corresponding answers that provide helpful information
3. Consider conversational context - answers might come several messages later

Return ONLY a valid JSON array with this exact format:
[{"question": question text (VERBATIM string), "answer": answer text (VERBATIM string), "question_user": user name (string), "answer_user": user name (string)}]"""
                },
                {
                    "role": "user", 
                    "content": f"Analyze this conversation:\n\n{conversation_text}"
                }
            ],
            max_tokens=1000,
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

def fetch_recent_messages(client, channel_id, max_messages=200):
    """Fetch recent messages from channel (rate-limit friendly)."""
    all_messages = []
    cursor = None
    fetched = 0
    
    print(f"📥 Fetching up to {max_messages} recent messages from {channel_id}...")
    
    while fetched < max_messages:
        try:
            batch_size = min(15, max_messages - fetched)
            resp = client.conversations_history(
                channel=channel_id,
                limit=batch_size,
                cursor=cursor
            )
            messages = resp["messages"]
            if not messages:
                break
                
            all_messages.extend(reversed(messages))
            fetched += len(messages)
            
            response_metadata = resp.get("response_metadata")
            cursor = response_metadata.get("next_cursor") if response_metadata else None
            
            if not cursor:
                break
                
            time.sleep(1)
            
        except SlackApiError as e:
            if e.response.status_code == 429:
                wait_time = int(e.response.headers.get("Retry-After", 60))
                print(f"⏳ Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time + 1)
                continue
            else:
                print(f"❌ Slack API error: {e}")
                break
    
    print(f"   ✅ Fetched {len(all_messages)} messages")
    return all_messages

def extract_qa_pairs(client, max_messages_per_channel=500):
    """Extract Q&A pairs using OpenAI analysis."""
    print("🚀 Starting Q&A extraction...")
    
    # Setup output
    OUT_DIR = Path("./out")
    OUT_DIR.mkdir(exist_ok=True, parents=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get channels
    channels_to_process = get_member_channels(client)
    print(f"Processing {len(channels_to_process)} channels")
    
    all_qa_pairs = []
    
    for channel_id in channels_to_process:
        print(f"🔍 Processing channel {channel_id}...")
        
        # Get recent messages
        messages = fetch_recent_messages(client, channel_id, max_messages_per_channel)
        if not messages:
            continue
        
        # Get user names
        user_ids = set(msg.get("user") for msg in messages if msg.get("user"))
        user_names = {}
        for user_id in user_ids:
            if user_id:
                user_names[user_id] = get_user_name(client, user_id)
        
        # Process in non-overlapping chunks
        CHUNK_SIZE = 20
        
        for i in range(0, len(messages), CHUNK_SIZE):
            chunk_messages = messages[i:i + CHUNK_SIZE]
            
            # Format for LLM
            formatted_messages = [format_message_for_llm(msg, user_names) for msg in chunk_messages]
            conversation_text = "\n".join(formatted_messages)
            
            # Skip short conversations
            if len(formatted_messages) < 2 or len(conversation_text.strip()) < 50:
                continue
            
            print(f"🤖 Analyzing {len(chunk_messages)} messages with OpenAI...")
            pairs = call_openai_for_qa_extraction(conversation_text)
            
            if pairs:
                print(f"   ✅ Found {len(pairs)} Q&A pairs")
                
            for pair in pairs:
                pair["channel"] = channel_id
                pair["timestamp"] = datetime.now().isoformat()
                all_qa_pairs.append(pair)
    
    # Save raw results
    raw_jsonl = OUT_DIR / f"qa_raw_{today}.jsonl"
    with raw_jsonl.open("w", encoding="utf-8") as jl:
        for pair in all_qa_pairs:
            jl.write(json.dumps(pair, ensure_ascii=False) + "\n")
    
    print(f"✅ Extracted {len(all_qa_pairs)} raw Q&A pairs")
    return all_qa_pairs, raw_jsonl

def deduplicate_qa_pairs(raw_jsonl_file):
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
    output_jsonl = Path(f"out/qa_deduplicated_{today}.jsonl")
    output_csv = Path(f"out/qa_deduplicated_{today}.csv")
    
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

def generate_faq_from_qa(qa_pairs):
    """Generate FAQ markdown from Q&A pairs."""
    print("📝 Generating FAQ markdown...")
    
    # Sort by question length (shorter questions first as they're often more common)
    qa_pairs.sort(key=lambda x: len(x.get("question", "")), reverse=False)
    
    # Categorize
    categories = defaultdict(list)
    
    for qa in qa_pairs:
        question = qa.get("question", "").lower()
        answer = qa.get("answer", "")
        
        if not answer or len(answer) < 10:
            continue
            
        if any(word in question for word in ["api", "endpoint", "token", "request", "call"]):
            categories["API & Authentication"].append(qa)
        elif any(word in question for word in ["credit", "pricing", "cost", "payment", "subscription"]):
            categories["Pricing & Credits"].append(qa)
        elif any(word in question for word in ["filter", "search", "query", "data"]):
            categories["Data & Filtering"].append(qa)
        elif any(word in question for word in ["linkedin", "post", "profile"]):
            categories["LinkedIn Data"].append(qa)
        elif any(word in question for word in ["limit", "rate", "usage", "error"]):
            categories["Limits & Troubleshooting"].append(qa)
        elif any(word in question for word in ["company", "companies", "screener"]):
            categories["Company Data"].append(qa)
        elif any(word in question for word in ["person", "people", "employee"]):
            categories["People Data"].append(qa)
        else:
            categories["General"].append(qa)
    
    # Generate FAQ
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = Path(f"out/FAQ_{today}.md")
    
    with open(output_file, 'w') as f:
        f.write("# Frequently Asked Questions (FAQ)\n\n")
        f.write(f"*Generated from Slack Q&A data on {today}*\n\n")
        f.write(f"This FAQ contains {len([qa for qa in qa_pairs if qa.get('answer') and len(qa.get('answer', '')) >= 10])} questions and answers extracted from internal Slack conversations.\n\n")
        
        # Table of Contents
        f.write("## Table of Contents\n\n")
        for category in sorted(categories.keys()):
            if categories[category]:
                f.write(f"- [{category}](#{category.lower().replace(' ', '-').replace('&', '')})\n")
        f.write("\n---\n\n")
        
        # Generate sections
        for category in sorted(categories.keys()):
            if not categories[category]:
                continue
                
            f.write(f"## {category}\n\n")
            
            question_num = 1
            for qa in categories[category]:
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                
                if not question or not answer:
                    continue
                
                question = question.strip()
                if not question.endswith("?"):
                    question += "?"
                
                answer = answer.strip()
                answer = re.sub(r'<@U[A-Z0-9]+>', '', answer)
                answer = re.sub(r'\s+', ' ', answer).strip()
                
                f.write(f"### {question_num}. {question}\n\n")
                f.write(f"{answer}\n\n")
                f.write("---\n\n")
                question_num += 1
        
        f.write("## Additional Information\n\n")
        f.write("This FAQ was automatically generated from Slack conversations using AI-powered extraction.\n")
        f.write("If you have questions not covered here, please reach out to the team.\n\n")
        f.write(f"*Last updated: {today}*\n")
    
    print(f"✅ FAQ generated: {output_file}")
    return output_file

def main():
    """Run the complete pipeline."""
    print("🚀 Starting complete Slack Q&A extraction pipeline\n")
    
    try:
        # Step 1: Setup
        print("Step 1: Setting up clients...")
        client, token = setup_clients()
        
        # Step 2: Extract Q&A pairs
        print("\nStep 2: Extracting Q&A pairs from Slack...")
        qa_pairs, raw_file = extract_qa_pairs(client)
        
        # Step 3: Deduplicate
        print("\nStep 3: Deduplicating Q&A pairs...")
        unique_qa, dedup_file = deduplicate_qa_pairs(raw_file)
        
        # Step 4: Generate FAQ
        print("\nStep 4: Generating FAQ markdown...")
        faq_file = generate_faq_from_qa(unique_qa)
        
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"📊 Final Results:")
        print(f"   Unique Q&A pairs: {len(unique_qa)}")
        print(f"   FAQ file: {faq_file}")
        print(f"   Deduplicated data: {dedup_file}")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()