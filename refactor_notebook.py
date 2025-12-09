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

# 1. Add Helper Functions (create_expanding_buttons, create_button_callback)
# We'll insert them early in the notebook, e.g. after 'load_raw_data'
print("Inserting Helper Functions...")
idx_helpers = find_cell_index(nb['cells'], "def load_raw_data(filepath):")
if idx_helpers != -1:
    helper_code = [
        "\n",
        "# --- Helper Functions from project.py ---\n",
        "def create_expanding_buttons(group_id, options, default_value):\n",
        "    \"\"\"\n",
        "    Creates a group of expanding buttons with a dcc.Store for state management.\n",
        "    \"\"\"\n",
        "    buttons = []\n",
        "    for opt in options:\n",
        "        value = opt['value']\n",
        "        label = opt['label']\n",
        "        is_active = (value == default_value)\n",
        "        \n",
        "        style = {\n",
        "            'flex-grow': '3' if is_active else '1',\n",
        "            'background-color': '#ff5722' if is_active else '#333',\n",
        "            'color': 'white' if is_active else '#888',\n",
        "            'padding': '10px',\n",
        "            'margin-right': '5px',\n",
        "            'border-radius': '5px',\n",
        "            'cursor': 'pointer',\n",
        "            'text-align': 'center',\n",
        "            'overflow': 'hidden',\n",
        "            'white-space': 'nowrap',\n",
        "            'transition': 'all 0.5s ease'\n",
        "        }\n",
        "        \n",
        "        buttons.append(html.Div(label, id=f'btn-{group_id}-{value}', n_clicks=0, style=style))\n",
        "\n",
        "    return html.Div([\n",
        "        dcc.Store(id=f'{group_id}-store', data=default_value),\n",
        "        html.Div(buttons, style={'display': 'flex', 'width': '100%', 'justify-content': 'center', 'marginBottom': '10px'})\n",
        "    ])\n",
        "\n",
        "def create_button_callback(group_id, options):\n",
        "    \"\"\"\n",
        "    Creates a callback for a group of expanding buttons.\n",
        "    \"\"\"\n",
        "    inputs = [Input(f'btn-{group_id}-{opt[\"value\"]}', 'n_clicks') for opt in options]\n",
        "    states = [State(f'btn-{group_id}-{opt[\"value\"]}', 'style') for opt in options]\n",
        "    \n",
        "    outputs = [Output(f'{group_id}-store', 'data')] + \\\n",
        "              [Output(f'btn-{group_id}-{opt[\"value\"]}', 'style') for opt in options]\n",
        "    \n",
        "    @app.callback(outputs, inputs, states)\n",
        "    def update_buttons(*args):\n",
        "        n_clicks = args[:len(options)]\n",
        "        styles = args[len(options):]\n",
        "        \n",
        "        ctx_msg = ctx.triggered_id\n",
        "        default_value = options[0]['value']\n",
        "        \n",
        "        if not ctx_msg:\n",
        "            return default_value, *styles\n",
        "\n",
        "        # Determine which button was clicked\n",
        "        clicked_value = default_value\n",
        "        for opt in options:\n",
        "            if f'btn-{group_id}-{opt[\"value\"]}' == ctx_msg:\n",
        "                clicked_value = opt['value']\n",
        "                break\n",
        "        \n",
        "        new_styles = []\n",
        "        for i, opt in enumerate(options):\n",
        "            style = styles[i].copy()\n",
        "            if opt['value'] == clicked_value:\n",
        "                style['flex-grow'] = '3'\n",
        "                style['background-color'] = '#ff5722'\n",
        "                style['color'] = 'white'\n",
        "            else:\n",
        "                style['flex-grow'] = '1'\n",
        "                style['background-color'] = '#333'\n",
        "                style['color'] = '#888'\n",
        "            new_styles.append(style)\n",
        "            \n",
        "        return clicked_value, *new_styles\n"
    ]
    # To check if already present
    source = nb['cells'][idx_helpers]['source']
    if "def create_expanding_buttons" not in "".join(source):
         nb['cells'][idx_helpers]['source'] = source + helper_code
         print("Helpers inserted.")
    else:
        print("Helpers already present.")
else:
    print("Warning: Could not find insertion point for helpers.")


# 2. Modify Layout to use Expanding Buttons
print("Modifying Layout...")
idx_layout = find_cell_index(nb['cells'], "dcc.Graph(id='vei-deaths-graph'")
if idx_layout != -1:
    source = nb['cells'][idx_layout]['source']
    new_source = []
    
    # We need to remove the previous buttons we added (btn-tsu-eq-count, btn-tsu-eq-norm)
    # and add the create_expanding_buttons call.
    
    skip_lines = False
    for line in source:
        # Detect start of our previous insertion
        if "# New Buttons for Tsunami & Earthquake" in line:
            skip_lines = True
            
        # Detect end of our previous insertion (approx)
        if "dcc.Store(id='heatmap-filter-store'" in line: # This was the last line of previous insertion
            skip_lines = False
            # Insert NEW Layout
            new_source.append("                    # Heatmap UI\n")
            new_source.append("                    html.Div([\n")
            new_source.append("                        create_expanding_buttons(\n")
            new_source.append("                            'heatmap',\n")
            new_source.append("                            [\n")
            new_source.append("                                {'label': 'Hazard (Tsu/Eq)', 'value': 'hazard'},\n")
            new_source.append("                                {'label': 'Hazard Risk', 'value': 'hazard_risk'},\n")
            new_source.append("                                {'label': 'Agent (All)', 'value': 'agent'},\n")
            new_source.append("                                {'label': 'Agent Risk', 'value': 'agent_risk'}\n")
            new_source.append("                            ],\n")
            new_source.append("                            'hazard' # Default\n")
            new_source.append("                        )\n")
            new_source.append("                    ]),\n")
            # We don't need 'heatmap-filter-store' anymore, we use 'heatmap-store' from creating_expanding_buttons
            continue 

        if skip_lines:
             if "dcc.Store(id='heatmap-filter-store'" in line: # Fallback if end detection missed in loop
                 skip_lines = False
             continue
        
        # Also remove old heatmap buttons if they still exist (unlikely if they were below)
        # But wait, create_expanding_buttons replaces the 'heatmap-store' logic I had.
        
        new_source.append(line)
        
    nb['cells'][idx_layout]['source'] = new_source
    print("Layout updated.")
else:
     print("Error: Layout cell not found.")

# 3. Update update_dashboard Callback
print("Updating update_dashboard Callback...")
idx_cb = find_cell_index(nb['cells'], "def update_dashboard(selected_country")
if idx_cb != -1:
    source = nb['cells'][idx_cb]['source']
    
    # 3a. Update Input from 'heatmap-filter-store' back to 'heatmap-store'
    for i, line in enumerate(source):
        if "Input('heatmap-filter-store', 'data')" in line:
            source[i] = line.replace("Input('heatmap-filter-store', 'data')", "Input('heatmap-store', 'data')")
            print("Input updated back to heatmap-store.")
        elif "Input('heatmap-store', 'data')" in line:
            # Already correct? Wait, my previous script didn't remove heatmap-store input?
            # It added heatmap-filter-input. 
            # If heatmap-store was already there, I now have duplicate Inputs if I renamed one?
            # Let's check: previously I updated 'region-dropdown' input to add 'heatmap-filter-store'
            pass

    # 3b. Update Signature (heatmap_filter -> selected_heatmap_metric)
    # Previously: selected_region, heatmap_filter):
    # Now: selected_region, selected_heatmap_metric):
    for i, line in enumerate(source):
        if "heatmap_filter):" in line:
            source[i] = line.replace("heatmap_filter):", "selected_heatmap_metric):")
            print("Signature updated.")

    # 3c. Update Logic
    # We need to map selected_heatmap_metric (hazard, hazard_risk, agent, agent_risk) 
    # to (subset_agents, normalize)
    
    # Locate the logic block
    insert_idx = -1
    for i, line in enumerate(source):
        if "fig_vei_deaths = volcano_type_vs_hasard_heatmap" in line:
            insert_idx = i
            break
            
    if insert_idx != -1:
        # We replace the single line call with logic block
        logic_block = [
             "    \n",
             "    # Heatmap Logic\n",
             "    subset_agents = None\n",
             "    normalize = False\n",
             "    \n",
             "    if selected_heatmap_metric == 'hazard':\n",
             "        subset_agents = ['Waves (Tsunami)', 'Seismic']\n",
             "        normalize = False\n",
             "    elif selected_heatmap_metric == 'hazard_risk':\n",
             "        subset_agents = ['Waves (Tsunami)', 'Seismic']\n",
             "        normalize = True\n",
             "    elif selected_heatmap_metric == 'agent_risk':\n",
             "        normalize = True\n",
             "    # Default 'agent' is None/False\n",
             "    \n",
             "    fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=normalize, subset_agents=subset_agents)\n"
        ]
        # Replace the old call
        source[insert_idx] = "" # clear old line
        source[insert_idx:insert_idx] = logic_block
        print("Callback logic updated.")
        
    nb['cells'][idx_cb]['source'] = source
else:
    print("Error: Callback cell not found.")


# 4. Register the new buttons callback AND remove the old custom callback
print("Registering buttons callback...")
# We need to call create_button_callback('heatmap', ...)
# We can add this call in the main block or after helper defs.
# Let's add it near __main__
idx_main = find_cell_index(nb['cells'], "if __name__ == '__main__':")
if idx_main != -1:
    # First, try to remove the previously added custom callback if it exists
    # It was added just before main.
    if idx_main > 0:
        prev_cell = nb['cells'][idx_main-1]
        if "def update_heatmap_filter" in "".join(prev_cell['source']):
             print("Removing old custom callback cell.")
             nb['cells'].pop(idx_main-1)
             idx_main -= 1 # Adjust index

    # Insert registration code
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
    nb['cells'].insert(idx_main, reg_code)
    print("Registration code inserted.")
else:
    print("Error: Main block not found.")

# Save
print(f"Saving to {file_path}...")
with open(file_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Done.")
