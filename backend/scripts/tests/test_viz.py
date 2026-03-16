import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, r"d:\AI\AI_Export_insights")

from backend.ai_agent.data_adapter import get_adapter
from backend.ai_agent.agents.visualization_agent import VisualizationAgent

async def run():
    adapter = get_adapter()
    data = adapter.execute_query('SELECT * FROM "vw_Customer_Project_Invoices" ORDER BY "TotalAfterDiscountInvoice" DESC NULLS LAST LIMIT 3')
    
    if not data:
        print("No data found")
        return
        
    print(f"Data row sample: {data[0]}")
    viz_agent = VisualizationAgent()
    viz = await viz_agent.generate(query="اذكر مشاريع الشهر الماضي", data=data)
    print("Viz:", viz)

if __name__ == "__main__":
    asyncio.run(run())
