import re
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class QuerySafetyGuard:
    """
    Standalone guard module that runs before the LLM processing agent.
    Detects overly broad queries that would cause table full-scans or agent iteration timeouts.
    """

    # Terms indicating a broad request
    BROAD_PATTERNS = [
        r"(كل|جميع) (الانشطة|العمليات|المشاريع|البيانات|الفواتير|الحسابات)",
        r"(show|list|get) all (activities|operations|projects|data|invoices|accounts)",
        r"اعرض كل",
        r"عرض كل",
        r"هات كل"
    ]

    # Prepositions before an entity name
    ENTITY_PREPOSITIONS = [
        r"الخاصة بـ\s*([^\s]{3,}.*)",
        r"لـ\s*([^\s]{3,}.*)",
        r"التابعة لـ\s*([^\s]{3,}.*)",
        r"عميل\s*([^\s]{3,}.*)",
        r"جهة\s*([^\s]{3,}.*)",
        r"من\s*([^\s]{3,}.*)",
        r"for\s+([A-Za-z0-9 ]+)",
        r"of\s+([A-Za-z0-9 ]+)"
    ]

    @classmethod
    def check(cls, query: str, thinking_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Check the query complexity and safety.
        Returns safety_level: SAFE, WARN, or BLOCK.
        """
        query_lower = query.lower()
        
        is_broad = False
        for pattern in cls.BROAD_PATTERNS:
            if re.search(pattern, query_lower):
                is_broad = True
                break

        entity_name = cls.extract_entity(query)
        
        # If it's a broad query but we found an entity, we can just WARN (and auto-apply the filter)
        if is_broad and entity_name:
            logger.info(f"[SAFETY GUARD] Broad query with entity filter: '{entity_name}'. Assigned WARN.")
            return {
                "safety_level": "WARN",
                "entity_filter": entity_name,
                "recommended_limit": 50
            }
            
        # If it's broad and has NO entity filter, we BLOCK to prevent timeouts
        if is_broad and not entity_name:
            logger.warning("[SAFETY GUARD] Unbounded broad query detected. Assigned BLOCK.")
            return {
                "safety_level": "BLOCK",
                "block_reason": "طلبك عام جداً وقد يستغرق وقتاً طويلاً للمعالجة أو يتجاوز الحد المسموح به.",
                "suggested_query": "حدد عميلاً (مثل: اعرض عمليات البنك العربي) أو فترة زمنية (مثل: إجمالي فواتير الشهر الماضي)."
            }

        # Otherwise, fully SAFE (e.g. specific questions, calculations, or explicitly constrained SQL)
        return {
            "safety_level": "SAFE",
            "entity_filter": entity_name,
            "recommended_limit": 50
        }

    @classmethod
    def extract_entity(cls, query: str) -> str:
        """
        Regex-based extraction of an entity name from the query text.
        """
        for pattern in cls.ENTITY_PREPOSITIONS:
            match = re.search(pattern, query)
            if match:
                extracted = match.group(1).strip()
                # Clean up trailing punctuation or time words
                extracted = re.sub(r'(\s+في\s+\d{4}|\s+خلال\s+.*|[\.\،\,]+)$', '', extracted)
                # Short entities under 2 chars are likely noise
                if len(extracted) > 2:
                    return extracted
        return None
