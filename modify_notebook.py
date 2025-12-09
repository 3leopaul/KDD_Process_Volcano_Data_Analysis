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

# 1. Modify volcano_type_vs_hasard_heatmap
print("Modifying volcano_type_vs_hasard_heatmap...")
idx = find_cell_index(nb['cells'], 'def volcano_type_vs_hasard_heatmap(df, normalize=False):')
if idx != -1:
    source = nb['cells'][idx]['source']
    # Replace signature
    for i, line in enumerate(source):
        if 'def volcano_type_vs_hasard_heatmap(df, normalize=False):' in line:
            source[i] = line.replace('normalize=False):', 'normalize=False, subset_agents=None):')
            
    # Insert filtering logic
    insert_idx = -1
    for i, line in enumerate(source):
        if 'agent_type_matrix = agent_type_matrix[final_cols]' in line:
             insert_idx = i
             break
    
    if insert_idx != -1:
        new_lines = [
            "    \n",
            "    # 4b. Filter by subset_agents if provided\n",
            "    if subset_agents:\n",
            "        # Keep only columns that are in subset_agents\n",
            "        final_cols = [c for c in final_cols if c in subset_agents]\n",
            "        if not final_cols:\n",
            "             fig = go.Figure()\n",
            "             fig.add_annotation(text=\"No Hazard Data (Filtered)\", x=0.5, y=0.5, showarrow=False, font=dict(color=\"gray\", size=20))\n",
            "             fig.update_layout(template=\"plotly_dark\", xaxis={'visible': False}, yaxis={'visible': False})\n",
            "             return fig\n",
            "    \n"
        ]
        source[insert_idx:insert_idx] = new_lines
        nb['cells'][idx]['source'] = source
        print("Function updated.")
    else:
        print("Error: Could not find insertion point in function.")
else:
    print("Error: Could not find function definition.")

# 2. Modify Layout
print("Modifying Layout...")
# Use a snippet that is unique to the layout cell (Dash graph id)
idx_layout = find_cell_index(nb['cells'], "dcc.Graph(id='vei-deaths-graph'")

if idx_layout != -1:
    source = nb['cells'][idx_layout]['source']
    insert_idx = -1
    for i, line in enumerate(source):
        if "dcc.Graph(id='vei-deaths-graph'" in line:
            insert_idx = i
            break
            
    if insert_idx != -1:
         new_lines = [
             "                    # New Buttons for Tsunami & Earthquake\n",
             "                    html.Div([\n",
             "                        html.Button('Tsunami & Earthquake (Count)', id='btn-tsu-eq-count', n_clicks=0, style={'margin-right': '10px', 'padding': '5px', 'cursor': 'pointer'}),\n",
             "                        html.Button('Tsunami & Earthquake (Normalized)', id='btn-tsu-eq-norm', n_clicks=0, style={'padding': '5px', 'cursor': 'pointer'})\n",
             "                    ], style={'marginTop': '10px', 'textAlign': 'center', 'marginBottom': '10px'}),\n",
             "                    dcc.Store(id='heatmap-filter-store', data=['Waves (Tsunami)', 'Seismic']), # Default Filter\n"
         ]
         source[insert_idx:insert_idx] = new_lines
         nb['cells'][idx_layout]['source'] = source
         print("Layout updated.")
    else:
        print("Error: Could not find insertion point in layout.")
else:
    print("Error: Could not find layout cell.")

# 3. Modify Callback
print("Modifying update_dashboard callback...")
idx_cb = find_cell_index(nb['cells'], "def update_dashboard(selected_country, year_range, selected_vei_metric")
if idx_cb != -1:
    source = nb['cells'][idx_cb]['source']
    
    # Update Signature
    sig_updated = False
    for i, line in enumerate(source):
        if "def update_dashboard(" in line:
            if "selected_region):" in line:
                source[i] = line.replace("selected_region):", "selected_region, heatmap_filter):")
                sig_updated = True
            elif "selected_region" in line and "):" in line: # Multi-line?
                 source[i] = line.replace("selected_region):", "selected_region, heatmap_filter):")
                 sig_updated = True
    
    if not sig_updated:
        # It handles the case where selected_region is the last arg.
        # Let's try simpler replacement if exact match fails
        pass

    # Update Input Decorator
    input_updated = False
    for i, line in enumerate(source):
        if "Input('region-dropdown', 'value')]" in line:
            source[i] = line.replace(")]", "),\n     Input('heatmap-filter-store', 'data')]")
            input_updated = True
            break
    
    # Update Function Call
    call_updated = False
    for i, line in enumerate(source):
        if "volcano_type_vs_hasard_heatmap" in line:
            # Need strict replacement to avoid breaking syntax
             if "percent'))" in line:
                 source[i] = line.replace("percent'))", "percent'), subset_agents=heatmap_filter)")
                 call_updated = True
             elif "percent' ))" in line: # Safety check
                 source[i] = line.replace("percent' ))", "percent' ), subset_agents=heatmap_filter)")
                 call_updated = True
    
    nb['cells'][idx_cb]['source'] = source
    print(f"Callback updated? Signature: {sig_updated}, Input: {input_updated}, Call: {call_updated}")
else:
    print("Error: Could not find callback cell.")


# 4. Add NEW Callback for buttons
print("Adding new button callback...")
idx_main = find_cell_index(nb['cells'], "if __name__ == '__main__':")
new_cell = {
 "cell_type": "code",
 "execution_count": None,
 "metadata": {},
 "outputs": [],
 "source": [
  "# Callback for Heatmap Filter Buttons\n",
  "from dash import ctx\n",
  "\n",
  "@app.callback(\n",
  "    [Output('heatmap-filter-store', 'data', allow_duplicate=True),\n",
  "     Output('heatmap-store', 'data', allow_duplicate=True)],\n",
  "    [Input('btn-tsu-eq-count', 'n_clicks'),\n",
  "     Input('btn-tsu-eq-norm', 'n_clicks'),\n",
  "     Input('btn-heatmap-count', 'n_clicks'),\n",
  "     Input('btn-heatmap-percent', 'n_clicks')],\n",
  "    prevent_initial_call=True\n",
  ")\n",
  "def update_heatmap_filter(n_tsu_count, n_tsu_norm, n_all_count, n_all_percent):\n",
  "    ctx_msg = ctx.triggered_id\n",
  "    if not ctx_msg:\n",
  "        return dash.no_update, dash.no_update\n",
  "    \n",
  "    if ctx_msg == 'btn-tsu-eq-count':\n",
  "        return ['Waves (Tsunami)', 'Seismic'], 'count'\n",
  "    elif ctx_msg == 'btn-tsu-eq-norm':\n",
  "        return ['Waves (Tsunami)', 'Seismic'], 'percent'\n",
  "    else:\n",
  "        # Reset to All Agents if standard buttons are clicked\n",
  "        return None, dash.no_update\n"
 ]
}

if idx_main != -1:
    nb['cells'].insert(idx_main, new_cell)
else:
    nb['cells'].append(new_cell)
print("New callback added.")

# Save
print(f"Saving to {file_path}...")
with open(file_path, 'w') as f:
    json.dump(nb, f, indent=1)
print("Done.")
