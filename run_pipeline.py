#!/usr/bin/env python
"""
Main entry point for the complete Slack Q&A extraction pipeline.
This is the file you should run to execute the complete pipeline.
"""
from qa_extractor import QAExtractor
from faq_generator import FAQGenerator


def main():
    """Run the complete pipeline."""
    print("🚀 Starting complete Slack Q&A extraction pipeline\n")
    
    try:
        # Initialize components
        qa_extractor = QAExtractor()
        faq_generator = FAQGenerator()
        
        # Step 1: Extract Q&A pairs
        print("Step 1: Extracting Q&A pairs from Slack...")
        qa_pairs, raw_file = qa_extractor.extract_qa_pairs()
        
        # Step 2: Deduplicate
        print("\nStep 2: Deduplicating Q&A pairs...")
        unique_qa, dedup_file = qa_extractor.deduplicate_qa_pairs(raw_file)
        
        # Step 3: Generate FAQ
        print("\nStep 3: Generating FAQ markdown...")
        faq_file = faq_generator.generate_faq_from_qa(unique_qa)
        
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