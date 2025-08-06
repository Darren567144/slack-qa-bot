#!/usr/bin/env python
"""
FAQ markdown generation from Q&A pairs.
"""
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from config_manager import PipelineConfig


class FAQGenerator:
    """Generates FAQ markdown from Q&A pairs."""
    
    def __init__(self):
        self.config = PipelineConfig()
    
    def categorize_qa_pairs(self, qa_pairs):
        """Categorize Q&A pairs by topic."""
        categories = defaultdict(list)
        
        for qa in qa_pairs:
            question = qa.get("question", "").lower()
            answer = qa.get("answer", "")
            
            if not answer or len(answer) < self.config.MIN_ANSWER_LENGTH:
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
        
        return categories
    
    def clean_text_for_markdown(self, text):
        """Clean text for markdown output."""
        # Remove user mentions
        text = re.sub(r'<@U[A-Z0-9]+>', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def generate_table_of_contents(self, categories):
        """Generate markdown table of contents."""
        toc = "## Table of Contents\n\n"
        for category in sorted(categories.keys()):
            if categories[category]:
                anchor = category.lower().replace(' ', '-').replace('&', '').replace('/', '')
                toc += f"- [{category}](#{anchor})\n"
        toc += "\n---\n\n"
        return toc
    
    def generate_category_section(self, category, qa_pairs):
        """Generate markdown section for a category."""
        section = f"## {category}\n\n"
        
        question_num = 1
        for qa in qa_pairs:
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            
            if not question or not answer:
                continue
            
            question = question.strip()
            if not question.endswith("?"):
                question += "?"
            
            answer = self.clean_text_for_markdown(answer)
            
            section += f"### {question_num}. {question}\n\n"
            section += f"{answer}\n\n"
            section += "---\n\n"
            question_num += 1
        
        return section
    
    def generate_faq_from_qa(self, qa_pairs):
        """Generate FAQ markdown from Q&A pairs."""
        print("📝 Generating FAQ markdown...")
        
        # Sort by question length (shorter questions first as they're often more common)
        qa_pairs.sort(key=lambda x: len(x.get("question", "")), reverse=False)
        
        # Categorize
        categories = self.categorize_qa_pairs(qa_pairs)
        
        # Generate FAQ
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = self.config.OUTPUT_DIR / f"FAQ_{today}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("# Frequently Asked Questions (FAQ)\n\n")
            f.write(f"*Generated from Slack Q&A data on {today}*\n\n")
            
            valid_qa_count = len([qa for qa in qa_pairs if qa.get('answer') and len(qa.get('answer', '')) >= self.config.MIN_ANSWER_LENGTH])
            f.write(f"This FAQ contains {valid_qa_count} questions and answers extracted from internal Slack conversations.\n\n")
            
            # Table of Contents
            f.write(self.generate_table_of_contents(categories))
            
            # Generate sections
            for category in sorted(categories.keys()):
                if not categories[category]:
                    continue
                
                section = self.generate_category_section(category, categories[category])
                f.write(section)
            
            # Footer
            f.write("## Additional Information\n\n")
            f.write("This FAQ was automatically generated from Slack conversations using AI-powered extraction.\n")
            f.write("If you have questions not covered here, please reach out to the team.\n\n")
            f.write(f"*Last updated: {today}*\n")
        
        print(f"✅ FAQ generated: {output_file}")
        return output_file