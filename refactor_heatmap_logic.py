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

# Update update_dashboard Callback Logic
print("Updating update_dashboard Callback Logic...")
idx_cb = find_cell_index(nb['cells'], "def update_dashboard(selected_country, year_range")
if idx_cb != -1:
    source = nb['cells'][idx_cb]['source']
    
    # We need to replace the logic block we added previously.
    # Previous Block Start: "    # Heatmap Logic\n"
    # To End of that block.
    
    # New Logic:
    # if selected_heatmap_metric == 'hazard':
    #     fig_vei_deaths = volcano_type_vs_secondary_heatmap(dff, normalize=False)
    # elif selected_heatmap_metric == 'hazard_risk':
    #     fig_vei_deaths = volcano_type_vs_secondary_heatmap(dff, normalize=True)
    # elif selected_heatmap_metric == 'agent':
    #     fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=False)
    # elif selected_heatmap_metric == 'agent_risk':
    #     fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=True)
    # else:
    #     fig_vei_deaths = volcano_type_vs_secondary_heatmap(dff, normalize=False)
    
    # Verify current content
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(source):
        if "# Heatmap Logic" in line:
            start_idx = i
        if "fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=normalize, subset_agents=subset_agents)" in line:
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        # Remove old block [start_idx : end_idx+1]
        
        # Create New Block
        new_block = [
            "    # Heatmap Logic (Updated)\n",
            "    if selected_heatmap_metric == 'hazard':\n",
            "        fig_vei_deaths = volcano_type_vs_secondary_heatmap(dff, normalize=False)\n",
            "    elif selected_heatmap_metric == 'hazard_risk':\n",
            "        fig_vei_deaths = volcano_type_vs_secondary_heatmap(dff, normalize=True)\n",
            "    elif selected_heatmap_metric == 'agent':\n",
            "        fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=False)\n",
            "    elif selected_heatmap_metric == 'agent_risk':\n",
            "        fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=True)\n",
            "    else:\n",
            "        # Default to hazard\n",
            "        fig_vei_deaths = volcano_type_vs_secondary_heatmap(dff, normalize=False)\n"
        ]
        
        # Replace
        # Note: slices are excluding end_idx usually for python, but we want to replace the line at end_idx too.
        source[start_idx : end_idx+1] = new_block
        print("Logic updated successfully.")
        
    else:
        print("Error: Could not locate previous heatmap logic block.")
        # Fallback: Searching for the function call line might be enough if comments changed?
        # But I added "# Heatmap Logic" myself in refactor_notebook.py so it should be there.
        pass

    nb['cells'][idx_cb]['source'] = source
else:
    print("Error: Callback cell not found.")

# Save
print(f"Saving to {file_path}...")
with open(file_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Done.")
