import os

file_path = r"D:\AI\AI_Export_insights\data\ERP_PostgreSQL.sql"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken line for 'Right of'
# We look for the pattern and replace it
# The pattern seen was 'Right of \n;
# We replace it with 'Right of Use / Usufruct')\n;
# Note: we need to be careful about matching.

if "'Right of \n;" in content:
    print("Found broken 'Right of' line. Fixing...")
    content = content.replace("'Right of \n;", "'Right of Use / Usufruct')\n;")
else:
    print("Could not find exact match for 'Right of \\n;'. Searching for partial...")
    # fallback partial match
    if "'Right of " in content:
        # Check context
        idx = content.find("'Right of ")
        print(f"Context: {content[idx:idx+20]}")

# Fix long index names causing truncation conflicts
replacements = [
    ("RequestForIndicativeQuotationImportClauses_RequestForIndicativeQuotationId", "ReqForIndQuotImpClauses_ReqForIndQuotId"),
    ("RequestForIndicativeQuotationImportClauses_OperationClauseId", "ReqForIndQuotImpClauses_OpClauseId")
]

for old, new in replacements:
    if old in content:
        print(f"Replacing long identifier: {old} -> {new}")
        content = content.replace(old, new)
    else:
        print(f"Warning: Could not find identifier {old}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done.")
