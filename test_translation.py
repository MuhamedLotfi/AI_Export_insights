"""
Test script for Arabic translation verification
Run: python test_translation.py
"""
import sys
sys.path.insert(0, '.')

from backend.ai_agent.translation_service import get_translation_service

def test_translation():
    ts = get_translation_service()
    
    # Test 1: Language detection
    print("=" * 50)
    print("TEST 1: Language Detection")
    print("=" * 50)
    
    test_ar = "ما هي أعلى المشاريع مبيعات؟"
    test_en = "What are the top selling projects?"
    
    print(f"Arabic text: '{test_ar}'")
    print(f"  Detected: {ts.detect_language(test_ar)}")
    
    print(f"\nEnglish text: '{test_en}'")
    print(f"  Detected: {ts.detect_language(test_en)}")
    
    # Test 2: Translation AR -> EN
    print("\n" + "=" * 50)
    print("TEST 2: Arabic -> English Translation")
    print("=" * 50)
    
    ar_to_translate = "ما هي أعلى المشاريع مبيعات؟"
    print(f"Original (AR): {ar_to_translate}")
    
    translated_en = ts.translate_to_english(ar_to_translate)
    print(f"Translated (EN): {translated_en}")
    
    # Test 3: Translation EN -> AR
    print("\n" + "=" * 50)
    print("TEST 3: English -> Arabic Translation")
    print("=" * 50)
    
    en_to_translate = "The top selling project is Project 59 with total sales of 32,600,000."
    print(f"Original (EN): {en_to_translate}")
    
    translated_ar = ts.translate_to_arabic(en_to_translate)
    print(f"Translated (AR): {translated_ar}")
    
    print("\n" + "=" * 50)
    print("Tests complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_translation()
