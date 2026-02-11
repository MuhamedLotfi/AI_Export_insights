"""
Thinking Agent - Query Analysis and Tool Selection
Analyzes user queries and determines the appropriate processing strategy
"""
import logging
from typing import Dict, Any, List, Optional
import re

from backend.config import DOMAIN_AGENTS

logger = logging.getLogger(__name__)


class ThinkingAgent:
    """Agent responsible for analyzing queries and planning execution"""
    
    def __init__(self):
        self.domain_configs = DOMAIN_AGENTS
    
    async def analyze(
        self,
        query: str,
        allowed_agents: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a query to determine:
        - Required domains
        - Query type (ranking, trend, comparison, etc.)
        - Tool to use (sql, calculator, rag)
        - Extracted parameters
        """
        logger.info(f"[THINKING AGENT] Analyzing query: {query}")
        
        # Determine required domains
        required_domains = self._identify_domains(query)
        
        # Filter to only allowed domains
        allowed_domains = [d for d in required_domains if d in allowed_agents]
        blocked_domains = [d for d in required_domains if d not in allowed_agents]
        
        # Classify query type
        query_type = self._classify_query_type(query)
        
        # Select appropriate tool
        tool = self._select_tool(query, query_type)
        
        # Extract parameters
        parameters = self._extract_parameters(query)
        
        # Build domain context
        domain_context = self._build_domain_context(allowed_domains)
        
        result = {
            "query": query,
            "required_domains": required_domains,
            "allowed_domains": allowed_domains,
            "blocked_domains": blocked_domains,
            "query_type": query_type,
            "tool": tool,
            "parameters": parameters,
            "domain_context": domain_context,
            "confidence": self._calculate_confidence(query_type, allowed_domains),
            "reasoning": self._generate_reasoning(query, query_type, tool, allowed_domains)
        }
        
        logger.info(f"[THINKING AGENT] Result: tool={tool}, domains={allowed_domains}, type={query_type}")
        
        return result
    
    # Arabic keyword → domain mapping for bilingual routing
    ARABIC_DOMAIN_KEYWORDS = {
        "projects": ["مشروع", "مشاريع", "حالة المشروع", "بيانات المشروع"],
        "sales": ["مبيعات", "إيرادات", "عميل", "فاتورة", "فواتير", "أمر بيع", "أوامر بيع", "توريد"],
        "inventory": ["مخزون", "مخازن", "كمية", "إعادة طلب"],
        "purchasing": ["مشتريات", "مورد", "موردين", "أمر شراء", "طلب شراء"],
        "accounting": ["تكلفة", "ربح", "هامش", "مالي", "محاسبة", "ضريبة"],
    }

    # Arabic query type keywords
    ARABIC_QUERY_TYPE_KEYWORDS = {
        "ranking": ["أعلى", "أفضل", "أكثر", "أقل", "أدنى", "ترتيب"],
        "aggregation": ["إجمالي", "مجموع", "عدد", "متوسط", "كم"],
        "trend": ["اتجاه", "شهري", "أسبوعي", "يومي", "نمو"],
        "comparison": ["مقارنة", "قارن", "بين", "فرق"],
        "general": ["عرض", "بيانات", "كل", "اعرض", "وضح", "ما هو", "ما هي"],
    }

    def _identify_domains(self, query: str) -> List[str]:
        """Identify which domains are relevant to the query (English + Arabic)"""
        query_lower = query.lower()
        domains = []
        
        # English keyword matching from config
        for domain_code, config in self.domain_configs.items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    if domain_code not in domains:
                        domains.append(domain_code)
                    break
        
        # Arabic keyword matching
        for domain_code, ar_keywords in self.ARABIC_DOMAIN_KEYWORDS.items():
            for keyword in ar_keywords:
                if keyword in query:
                    if domain_code not in domains:
                        domains.append(domain_code)
                    break
        
        # Default to projects if no domain detected (since project_59 is the main data)
        if not domains:
            domains = ["projects"]
        
        return domains
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query (English + Arabic)"""
        query_lower = query.lower()
        
        # Ranking queries
        if any(kw in query_lower for kw in ["top", "best", "highest", "lowest", "most", "least"]):
            return "ranking"
        
        # Trend queries
        if any(kw in query_lower for kw in ["trend", "over time", "monthly", "weekly", "daily", "growth"]):
            return "trend"
        
        # Comparison queries
        if any(kw in query_lower for kw in ["compare", "vs", "versus", "difference", "between"]):
            return "comparison"
        
        # Aggregation queries
        if any(kw in query_lower for kw in ["total", "sum", "count", "average", "mean"]):
            return "aggregation"
        
        # Distribution queries
        if any(kw in query_lower for kw in ["distribution", "breakdown", "by category", "percentage"]):
            return "distribution"
        
        # Calculation queries
        if any(kw in query_lower for kw in ["calculate", "compute", "what is", "how much"]):
            return "calculation"
        
        # Arabic query type matching
        for qtype, ar_keywords in self.ARABIC_QUERY_TYPE_KEYWORDS.items():
            if any(kw in query for kw in ar_keywords):
                return qtype
        
        # Default to general query
        return "general"
    
    def _select_tool(self, query: str, query_type: str) -> str:
        """Select the appropriate tool for the query"""
        query_lower = query.lower()
        
        # Calculator for explicit calculations
        if any(kw in query_lower for kw in ["calculate", "%", "percent", "multiply", "divide"]):
            return "calculator"
        
        # SQL for data queries
        if query_type in ["ranking", "trend", "comparison", "aggregation", "distribution"]:
            return "sql"
        
        # RAG for knowledge queries
        if any(kw in query_lower for kw in ["explain", "what is", "how to", "why"]):
            return "rag"
        
        # Default to SQL
        return "sql"
    
    def _extract_parameters(self, query: str) -> Dict[str, Any]:
        """Extract parameters from the query"""
        params = {}
        query_lower = query.lower()
        
        # Extract limit/top N
        limit_patterns = [
            r"top (\d+)",
            r"(\d+) items",
            r"limit (\d+)",
            r"first (\d+)"
        ]
        for pattern in limit_patterns:
            match = re.search(pattern, query_lower)
            if match:
                params["limit"] = int(match.group(1))
                break
        
        # Extract date ranges
        date_patterns = [
            r"last (\d+) (days|weeks|months|years)",
            r"in (january|february|march|april|may|june|july|august|september|october|november|december)",
            r"(\d{4})"
        ]
        for pattern in date_patterns:
            match = re.search(pattern, query_lower)
            if match:
                params["date_context"] = match.group(0)
                break
        
        # Extract location
        location_patterns = [
            r"in (\w+) warehouse",
            r"from (\w+)",
            r"at (\w+) location"
        ]
        for pattern in location_patterns:
            match = re.search(pattern, query_lower)
            if match:
                params["location"] = match.group(1)
                break
        
        # Extract order direction
        if any(kw in query_lower for kw in ["highest", "most", "best", "top"]):
            params["order"] = "desc"
        elif any(kw in query_lower for kw in ["lowest", "least", "worst", "bottom"]):
            params["order"] = "asc"
        
        return params
    
    def _build_domain_context(self, domains: List[str]) -> Dict[str, Any]:
        """Build domain-specific context for processing"""
        tables = []
        sql_hints = []
        
        for domain in domains:
            config = self.domain_configs.get(domain, {})
            tables.extend(config.get("tables", []))
            if domain == "sales":
                sql_hints.append("Use 'amount' or 'total' columns for revenue calculations")
            elif domain == "inventory":
                sql_hints.append("Use 'quantity' for stock levels, positive = inbound, negative = outbound")
            elif domain == "purchasing":
                sql_hints.append("Check 'lead_time' for vendor performance")
            elif domain == "accounting":
                sql_hints.append("Use 'cost_price' and 'sell_price' for margin calculations")
        
        return {
            "tables": list(set(tables)),
            "sql_hints": sql_hints,
            "primary_domain": domains[0] if domains else None
        }
    
    def _calculate_confidence(self, query_type: str, domains: List[str]) -> str:
        """Calculate confidence level for the analysis"""
        if query_type == "general" or not domains:
            return "low"
        elif query_type in ["ranking", "aggregation"] and len(domains) == 1:
            return "high"
        elif len(domains) > 2:
            return "medium"
        else:
            return "high"
    
    def _generate_reasoning(
        self,
        query: str,
        query_type: str,
        tool: str,
        domains: List[str]
    ) -> str:
        """Generate reasoning explanation for the analysis"""
        reasoning = f"Query classified as '{query_type}' type. "
        reasoning += f"Selected '{tool}' tool for processing. "
        
        if domains:
            reasoning += f"Identified domains: {', '.join(domains)}. "
        
        if tool == "sql":
            reasoning += "Will generate SQL query to fetch relevant data."
        elif tool == "calculator":
            reasoning += "Will perform mathematical calculations."
        elif tool == "rag":
            reasoning += "Will search knowledge base for relevant information."
        
        return reasoning
