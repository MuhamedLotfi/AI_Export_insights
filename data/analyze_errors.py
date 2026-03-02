import re

with open('upsert_errors.log', 'r', encoding='utf-8') as f:
    text = f.read()

errors = re.findall(r'Error: (.+)', text)
queries = re.findall(r'Query: (.*?)\n', text)

missing_cols = set()
missing_tables = set()
other_errors = set()

for i, err in enumerate(errors):
    m = re.search(r'column "(.*?)" of relation "(.*?)" does not exist', err)
    if m:
        missing_cols.add(f"Table: {m.group(2)}, Column: {m.group(1)}")
    else:
        m2 = re.search(r'relation "(.*?)" does not exist', err)
        if m2:
            missing_tables.add(m2.group(1))
        else:
            other_errors.add(repr(err))

print("Missing columns:", missing_cols)
print("Missing tables:", missing_tables)
print("Other errors:", set([e[:100] for e in other_errors]))
