import json
import os

file_path = '/home/leopa/projects/KDD_Process_Volcano_Data_Analysis/main.ipynb'
print(f"Loading {file_path}...")

with open(file_path, 'r') as f:
    nb = json.load(f)

# Helper to find cell by unique content
def find_cell_index(cells, content_snipped):
    for i, cell in enumerate(cells):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if content_snipped in source:
                return i
    return -1

# Fix Imports
print("Fixing Imports...")
idx_import = find_cell_index(nb['cells'], "from dash import Dash, dcc, html, Input, Output, dash_table")
if idx_import != -1:
    source = nb['cells'][idx_import]['source']
    # We want to add State, ctx if missing
    new_source = []
    for line in source:
        if "from dash import Dash" in line:
            # Replace with full list
            new_line = "from dash import Dash, dcc, html, Input, Output, State, ctx, dash_table\n"
            new_source.append(new_line)
            print("Imports updated to include State and ctx.")
        else:
            new_source.append(line)
    
    nb['cells'][idx_import]['source'] = new_source
else:
    print("Error: Import cell not found.")

# Save
print(f"Saving to {file_path}...")
with open(file_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Done.")
