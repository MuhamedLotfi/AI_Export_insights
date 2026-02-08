"""
Translation Service - Arabic ↔ English Translation using TranslateGemma
Provides bidirectional translation for Arabic (ar-EG) language support
"""
import logging
import re
from typing import Optional
import ollama

from backend.config import AI_CONFIG

logger = logging.getLogger(__name__)


class TranslationService:
    """Handles Arabic ↔ English translation using TranslateGemma model"""
    
    # Arabic Unicode range pattern
    ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    
    def __init__(self):
        self.model = AI_CONFIG.get("translation_model", "translategemma:4b")
        self.enabled = AI_CONFIG.get("translation_enabled", True)
        logger.info(f"TranslationService initialized with model: {self.model}")
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is primarily Arabic or English
        Returns: "ar" for Arabic, "en" for English
        """
        if not text:
            return "en"
        
        # Count Arabic characters (each individual character in Arabic Unicode range)
        arabic_char_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or '\u08A0' <= c <= '\u08FF')
        total_alpha = sum(1 for c in text if c.isalpha())
        
        if total_alpha == 0:
            return "en"
        
        # If more than 30% Arabic characters, consider it Arabic
        arabic_ratio = arabic_char_count / total_alpha if total_alpha > 0 else 0
        
        detected = "ar" if arabic_ratio > 0.3 else "en"
        logger.info(f"[TRANSLATION] Language detected: {detected} (Arabic chars: {arabic_char_count}/{total_alpha}, ratio: {arabic_ratio:.2f})")
        
        return detected
    
    def translate_to_english(self, text: str) -> str:
        """
        Translate Arabic text to English using professional translator prompt
        """
        if not self.enabled or not text:
            return text
        
        try:
            logger.info(f"[TRANSLATION] AR → EN: {text[:50]}...")
            
            # Professional translator prompt for Arabic to English
            prompt = f"You are a professional Arabic (ar) to English (en) translator. Your goal is to accurately convey the meaning and nuances of the original Arabic text while adhering to English grammar, vocabulary, and cultural sensitivities. Produce only the English translation, without any additional explanations or commentary. Please translate the following Arabic text into English:\n{text}"
            
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                keep_alive="10m"
            )
            
            translated = response['message']['content'].strip()
            logger.info(f"[TRANSLATION] Result: {translated[:50]}...")
            
            return translated
            
        except Exception as e:
            logger.error(f"[TRANSLATION] Error translating to English: {e}")
            return text  # Return original on error
    
    def translate_to_arabic(self, text: str) -> str:
        """
        Translate English text to Arabic (ar-EG) using professional translator prompt
        """
        if not self.enabled or not text:
            return text
        
        try:
            logger.info(f"[TRANSLATION] EN → AR: {text[:50]}...")
            
            # Professional translator prompt for English to Arabic
            prompt = f"You are a professional English (en) to Arabic (ar) translator. Your goal is to accurately convey the meaning and nuances of the original English text while adhering to Arabic grammar, vocabulary, and cultural sensitivities. Produce only the Arabic translation, without any additional explanations or commentary. Please translate the following English text into Arabic:\n{text}"
            
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                keep_alive="10m"
            )
            
            translated = response['message']['content'].strip()
            logger.info(f"[TRANSLATION] Result: {translated[:50]}...")
            
            return translated
            
        except Exception as e:
            logger.error(f"[TRANSLATION] Error translating to Arabic: {e}")
            return text  # Return original on error


# Singleton instance
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get or create the translation service singleton"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
