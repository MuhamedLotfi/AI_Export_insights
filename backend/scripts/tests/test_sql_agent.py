import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_agent.agents.processing_agent import ProcessingAgent
from backend.config import DATA_SOURCE

async def test_sql_agent():
    print(f"Testing SQL Agent with DATA_SOURCE={DATA_SOURCE}")
    
    agent = ProcessingAgent()
    
    # Test query
    query = "How many users are active?"
    domain_context = {"tables": ["Users"]}
    parameters = {}
    
    print(f"Executing query: {query}")
    result = await agent.execute(query, {"tool": "sql", "domain_context": domain_context, "parameters": parameters}, [])
    
    print("Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_sql_agent())
