"""
Test script to verify dynamic table discovery in ThinkingAgent
"""
import sys
import os
import asyncio
import logging

# Add project root to path (D:\AI\AI_Export_insights)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.ai_agent.agents.thinking_agent import ThinkingAgent
from backend.config import DOMAIN_AGENTS

async def test_discovery():
    logger.info("Initializing ThinkingAgent...")
    agent = ThinkingAgent()
    
    # Test 1: Sales Query
    query = "Show me top 5 sales revenue"
    logger.info(f"\n--- Testing Query: '{query}' ---")
    
    # All agents allowed
    allowed = list(DOMAIN_AGENTS.keys())
    
    result = await agent.analyze(query, allowed)
    
    print(f"Required Domains: {result['required_domains']}")
    print(f"Selected Tool: {result['tool']}")
    print(f"Domain Context Tables: {result['domain_context'].get('tables')}")
    
    tables = result['domain_context'].get('tables', [])
    if any(t.lower() in ["entityinvoices", "invoices", "sales"] for t in tables):
        print("✅ SUCCESS: Found sales-related tables (EntityInvoices)!")
    else:
        print(f"❌ FAILURE: Did not find sales tables. Found: {tables}")

    # Test 2: Project Query
    query = "Show me project stats"
    logger.info(f"\n--- Testing Query: '{query}' ---")
    
    result = await agent.analyze(query, allowed)
    print(f"Domain Context Tables: {result['domain_context'].get('tables')}")
    
    tables = result['domain_context'].get('tables', [])
    if any(t.lower() in ["operations", "project_59", "projects"] for t in tables):
         print("✅ SUCCESS: Found project tables (Operations)!")
    else:
         print(f"❌ FAILURE: Did not find project tables. Found: {tables}")

if __name__ == "__main__":
    asyncio.run(test_discovery())
