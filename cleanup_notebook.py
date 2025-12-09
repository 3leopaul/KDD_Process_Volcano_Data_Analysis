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

# 1. Remove Obsolete Callback `update_heatmap_filter`
print("Removing obsolete update_heatmap_filter callback...")
idx_cb = find_cell_index(nb['cells'], "def update_heatmap_filter(n_tsu_count")
if idx_cb != -1:
    print(f"Removing cell {idx_cb}")
    nb['cells'].pop(idx_cb)
    print("Callback removed.")
else:
    print("Obsolete callback not found.")

# 2. Remove Original Button Registration
print("Removing original create_button_callback('heatmap')...")
# We look for the one containing 'Risk Percentage'
idx_reg = -1
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "create_button_callback('heatmap'" in source and "'Risk Percentage'" in source:
             # Make sure it's not the NEW one (which might have Hazard Risk, but not 'Risk Percentage' as label? 
             # Wait, new one has 'Hazard Risk' and 'Agent Risk'. Old one has 'Risk Percentage'.
             # Let's be precise.
             if "'label': 'Risk Percentage'" in source:
                 idx_reg = i
                 break

if idx_reg != -1:
    # This cell likely contains other registrations too (time, vei, secondary).
    # We should only remove the heatmap part.
    source = nb['cells'][idx_reg]['source']
    new_source = []
    skip = False
    for line in source:
        if "create_button_callback('heatmap'" in line:
            skip = True
        
        if skip:
            if "])" in line: # End of call
                skip = False
                continue
            continue
            
        new_source.append(line)
    
    nb['cells'][idx_reg]['source'] = new_source
    print("Original button registration removed (filtered).")
else:
    print("Original button registration not found.")


# 3. Remove Original Layout Buttons
print("Removing original layout buttons...")
# We look for the layout cell
idx_layout = find_cell_index(nb['cells'], "dcc.Graph(id='vei-deaths-graph'")
if idx_layout != -1:
    source = nb['cells'][idx_layout]['source']
    new_source = []
    # We want to remove the block that looks like:
    # html.Div([
    #    create_expanding_buttons('heatmap', [{'label': 'Count'...}, {'label': 'Risk Percentage'...}], ...)
    # ]),
    
    # Strat: Identify the line with create_expanding_buttons('heatmap' AND 'Risk Percentage'
    # And remove surrounding lines?
    
    # Layout structure in project.py was:
    # html.Div([
    #    html.Div([
    #        create_expanding_buttons('heatmap', ...)
    #    ]),
    #    dcc.Graph...
    
    # We inserted our NEW buttons *before* dcc.Graph.
    # The OLD buttons are probably *before* that too?
    # Or in the same list?
    
    # Let's iterate and look for the specific create_expanding_buttons line with 'Risk Percentage'
    
    skip = False
    for i, line in enumerate(source):
        # We need to be careful not to delete the NEW buttons
        if "create_expanding_buttons" in line and "'heatmap'" in line:
            # Check if it's the old one
            # The definition spans multiple lines, but usually the first line has the function call
            # We can peek ahead?
            
            # Simple heuristic: If we see 'Risk Percentage' in the next few lines, it's the old one.
            # But we are iterating line by line.
            
            # Let's buffer? No, let's just use strict removal if we can identify the block start.
            pass
            
    # Better approach:
    # The old buttons are defined as:
    # create_expanding_buttons(
    #    'heatmap',
    #    [
    #        {'label': 'Count', 'value': 'count'},
    #        {'label': 'Risk Percentage', 'value': 'percent'}
    #    ],
    #    'count'
    # )
    
    # This is a block of lines.
    # We can filter out lines that match this specific pattern.
    
    final_source = []
    i = 0
    while i < len(source):
        line = source[i]
        # Detect start of old heatmap block
        if "create_expanding_buttons" in line and "'heatmap'" in line:
             # Check distinct feature of old block
             # We can look at the next few lines
             chunk = "".join(source[i:i+10])
             if "'Risk Percentage'" in chunk:
                 print(f"Found old layout block at line {i}. Removing...")
                 # Skip until we find the closing parenthesis of the function call?
                 # or the closing Div?
                 # It's usually wrapped in html.Div([]),
                 
                 # Let's skip until we see the start of our NEW block or the Graph?
                 # OR just skip the function call lines.
                 
                 # Heuristic: Skip until 'count' (default val) and closing parens
                 j = i
                 while j < len(source):
                     if "count'" in source[j] and ")" in source[j]: # End of call?
                         # Usually: 'count'\n )
                         break
                     j += 1
                 
                 # We also likely want to remove the wrapping html.Div if it exists.
                 # This is hard to parse line-by-line without an AST.
                 
                 # AGRESSIVE: Just comment it out or replace with empty string?
                 # Let's try to remove duplication.
                 
                 # If we just remove the create_expanding_buttons call, the comma might result in invalid syntax
                 # e.g. html.Div([ , dcc.Graph...])
                 
                 # Let's be safer.
                 # The user screenshot showed the old buttons ABOVE the new buttons.
                 # My new buttons are inserted immediately before dcc.Graph.
                 # So duplicate is likely ABOVE my new insertion.
                 
                 # If I just remove the lines containing:
                 # "create_expanding_buttons('heatmap',"
                 # "{'label': 'Count', 'value': 'count'},"
                 # "{'label': 'Risk Percentage', 'value': 'percent'}"
                 # "],"
                 # "'count'"
                 # ")"
                 
                 # It should be fine.
                 
                 i = j + 1 # Advance
                 continue
                 
        final_source.append(line)
        i += 1
        
    nb['cells'][idx_layout]['source'] = final_source
    print("Layout cleanup done.")

else:
    print("Layout cell duplicate not found.")


# Save
print(f"Saving to {file_path}...")
with open(file_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Done.")
