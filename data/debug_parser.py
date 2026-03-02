import re

SQL_FILE = r"D:\AI\AI_Export_insights\data\ERP2202_PostgreSQL.sql"

print("Reading SQL script...")
with open(SQL_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Split by newline, correctly handling strings
print("Parsing lines...")
statements = []
current_line = []
inside_string = False
for char in content:
    if char == "'":
        inside_string = not inside_string
    if char == '\n' and not inside_string:
        s = "".join(current_line).strip()
        if s:
            statements.append(s)
        current_line = []
    else:
        current_line.append(char)
if current_line:
    s = "".join(current_line).strip()
    if s:
        statements.append(s)
        
insert_pattern = re.compile(r'INSERT\s+INTO\s+public\."([^"]+)"\s*\(([^)]+)\)\s*VALUES\s*(.*)', re.IGNORECASE | re.DOTALL)

success_count = 0
not_start = 0
not_match = 0
match_cases = 0

print(f"Found {len(statements)} statements.")

for stmt in statements:
    if not stmt.upper().startswith('INSERT INTO'):
        not_start += 1
        if not_start < 5:
            print("NOT START:", repr(stmt[:50]))
        continue

    match = insert_pattern.match(stmt)
    if not match:
        not_match += 1
        if not_match < 5:
            print("NOT MATCH:", repr(stmt[:50]))
        continue

    match_cases += 1
    
print(f"not_start: {not_start}, not_match: {not_match}, match_cases: {match_cases}")
