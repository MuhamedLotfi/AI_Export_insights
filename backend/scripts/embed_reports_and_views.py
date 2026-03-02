import sys
import os
import glob
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.ai_agent.vector_service import get_vector_service
from backend.ai_agent.data_adapter import get_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def embed_reports():
    logger.info("Starting Reports and Views embedding...")
    vector = get_vector_service()
    if not vector._ready:
        logger.error("Vector service not ready.")
        return
        
    adapter = get_adapter()
    
    # 1. Embed Master Views Schema
    logger.info("Embedding Core Views Metadata...")
    views_description = {
        "vw_Customer_Project_Invoices": "MASTER VIEW for Customer/Client Invoices, Revenue, and Project Status. Keywords: revenue, invoice, project, sales, customer, ايراد, فاتورة, مشروع, مبيعات",
        "vw_Supplier_Project_Invoices": "MASTER VIEW for Supplier Invoices, Project Costs, and Subcontractors. Keywords: cost, supplier, purchase, invoice, project, تكلفة, مورد, فاتورة, مشروع, مشتريات"
    }
    
    # We fetch schema columns via raw SQL because adapter might not list views directly
    import psycopg2
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="ERP_AI",
            user="postgres",
            password="postgres_erp",
            port=5432
        )
        cur = conn.cursor()
        
        for view_name, desc in views_description.items():
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{view_name.lower()}' 
                ORDER BY ordinal_position;
            """)
            cols = [row[0] for row in cur.fetchall()]
            if cols:
                content = f"Table: {view_name}\nColumns: {', '.join(cols)}\nDescription: {desc}"
                vector.index_row(
                    table_name="__schema_metadata__",
                    row_id=view_name,
                    content=content,
                    metadata={"table": view_name, "columns": cols, "is_view": True}
                )
                logger.info(f"Embedded view schema: {view_name}")
            else:
                logger.warning(f"Could not find columns for {view_name}")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error reading view schemas: {e}")

    # 2. Embed SQL Reports
    logger.info("Embedding SQL Report Scripts...")
    reports_dir = r"d:\AI\AI_Export_insights\data\reports"
    sql_files = glob.glob(os.path.join(reports_dir, "*.sql"))
    
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        # Create a highly relevant chunk of text
        content = f"High priority SQL Report/Query: {filename}\n{sql_content[:1000]}..." 
        
        vector.index_row(
            table_name="__schema_metadata__",
            row_id=f"report_{filename}",
            content=content,
            metadata={"table": "SQL_Reports_Knowledge", "filename": filename, "type": "sql_report"}
        )
        logger.info(f"Embedded SQL report: {filename}")
        
    logger.info("✅ Finished embedding reports and views!")

if __name__ == "__main__":
    embed_reports()
