import re

FILE = r"D:\AI\AI_Export_insights\data\ERP_PostgreSQL.sql"
PATTERN = "IX_RequestForIndicativeQuotationImportClauses"

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
found = []
for i, line in enumerate(lines):
    if PATTERN in line:
        found.append((i+1, line.strip()))
        
for idx, text in found:
    print(f"Line {idx}: {text}")
