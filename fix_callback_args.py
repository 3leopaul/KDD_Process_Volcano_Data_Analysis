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

# Fix update_dashboard Callback
print("Fixing update_dashboard Callback...")
idx_cb = find_cell_index(nb['cells'], "def update_dashboard(selected_country, year_range")
if idx_cb != -1:
    source = nb['cells'][idx_cb]['source']
    
    # 1. Detect and Remove duplicate Input('heatmap-store', 'data')]
    # We expect it at the end.
    
    dup_idx = -1
    for i in range(len(source)-1, -1, -1):
        if "Input('heatmap-store', 'data')]" in source[i]:
            dup_idx = i
            break
            
    if dup_idx != -1:
        # Check if there is another one earlier
        has_earlier = False
        for i in range(dup_idx):
             if "Input('heatmap-store', 'data')" in source[i]:
                 has_earlier = True
                 break
        
        if has_earlier:
            print(f"Removing duplicate input at line {dup_idx}")
            # We need to make sure the previous line has a closing bracket if we remove this one? 
            # OR, if this was the last item in the list, the previous item needs to lose its trailing comma and gain a closing bracket?
            
            # Use strict text replacement for safety
            # The line to remove: "     Input('heatmap-store', 'data')] \n"
            # The line before it: "     Input('region-dropdown', 'value'),\n"
            
            # Actually, let's just remove the line.
            # But we must ensure the list is closed properly.
            # source[dup_idx] is the LAST input. 
            # source[dup_idx-1] is "Input('region-dropdown', 'value'),\n"
            
            # Simple Fix: Change source[dup_idx-1] to close the list.
            if "Input('region-dropdown', 'value')," in source[dup_idx-1]:
                source[dup_idx-1] = source[dup_idx-1].replace("value'),", "value')]")
                source.pop(dup_idx)
                print("List closure fixed and duplicate removed.")
            else:
                 print("Warning: Previous line structure unexpected. Aborting specific fix.")
                 # Fallback: Just remove the line if it has the closing bracket?
                 # If we remove "Input('heatmap-store', 'data')]", the previous line ends with comma.
                 # Python accepts trailing commas in lists usually, but this is inside a function call arguments?
                 # app.callback([Output...], [Input...])
                 # The Input list is [ ... ].
                 # If we remove the last item, the previous item "...," is fine in Python list.
                 # BUT we need to close the list "]" parenthesis.
                 
                 # Let's inspect source[dup_idx-1] again.
                 # If source[dup_idx] = "     Input('heatmap-store', 'data')] \n"
                 # It contains the closing bracket.
                 # So if we remove it, we lose the closing bracket.
                 # So we MUST add the closing bracket to the previous line.
                 pass
        else:
            print("No earlier heatmap-store input found. Not a duplicate?")
    else:
        print("Duplicate input not found at end.")

    nb['cells'][idx_cb]['source'] = source
else:
    print("Error: Callback cell not found.")

# Save
print(f"Saving to {file_path}...")
with open(file_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Done.")
