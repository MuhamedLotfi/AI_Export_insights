import re
import json

INPUT_FILE = r"D:\AI\AI_Export_insights\data\ERP.sql"
OUTPUT_FILE = r"D:\AI\AI_Export_insights\data\bit_columns.json"

def scan():
    tables = {}
    current_table = None
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Detect Table Creation
            # CREATE TABLE [dbo].[TableName](
            m_table = re.match(r'CREATE\s+TABLE\s+\[dbo\]\.\[(.*?)\]', line, re.IGNORECASE)
            if m_table:
                current_table = m_table.group(1)
                tables[current_table] = []
                continue
                
            if current_table:
                # Detect Column with [bit]
                # [ColName] [bit] ...
                m_col = re.match(r'\[(.*?)\]\s+\[bit\]', line, re.IGNORECASE)
                if m_col:
                    col_name = m_col.group(1)
                    tables[current_table].append(col_name)
                
                # Detect End of Table
                if line.startswith(')'):
                    current_table = None
                    
    # Filter empty tables
    tables = {k: v for k, v in tables.items() if v}
    
    print(f"Found {len(tables)} tables with BIT columns.")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(tables, f, indent=2)

if __name__ == "__main__":
    scan()
