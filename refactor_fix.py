import json
import os

file_path = '/home/leopa/projects/KDD_Process_Volcano_Data_Analysis/main.ipynb'
print(f"Loading {file_path}...")

with open(file_path, 'r') as f:
    nb = json.load(f)

def find_cell_index(cells, content_snipped):
    for i, cell in enumerate(cells):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if content_snipped in source:
                return i
    return -1

print("Registering buttons callback (Fix)...")
idx_app_run = find_cell_index(nb['cells'], "app.run(")

if idx_app_run == -1:
    idx_app_run = find_cell_index(nb['cells'], "app.run_server(")

if idx_app_run != -1:
    # Insert before app.run
    reg_code = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
             "# Register Heatmap Buttons Callback\n",
             "create_button_callback('heatmap', [\n",
             "    {'label': 'Hazard (Tsu/Eq)', 'value': 'hazard'},\n",
             "    {'label': 'Hazard Risk', 'value': 'hazard_risk'},\n",
             "    {'label': 'Agent (All)', 'value': 'agent'},\n",
             "    {'label': 'Agent Risk', 'value': 'agent_risk'}\n",
             "])\n"
        ]
    }
    nb['cells'].insert(idx_app_run, reg_code)
    print("Registration code inserted.")
else:
    print("Error: app.run cell not found. Appending to end.")
    nb['cells'].append(reg_code)

# Save
print(f"Saving to {file_path}...")
with open(file_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Done.")
