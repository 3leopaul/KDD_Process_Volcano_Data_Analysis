import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np

def load_data(filepath="volcano-events.tsv"):
    try:
        df = pd.read_csv(filepath, sep='\t')
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return pd.DataFrame()

    df.rename(columns={
        'Damage ($Mil)': 'Damage_Millions',
        'Total Damage ($Mil)': 'Total_Damage_Millions',
        'Elevation (m)': 'Elevation',
        'Total Deaths': 'Total_Deaths',
        'Total Injuries': 'Total_Injuries'
    }, inplace=True)

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df.dropna(subset=['Year'], inplace=True)
    df['VEI'] = pd.to_numeric(df['VEI'], errors='coerce')
    df['Deaths'] = pd.to_numeric(df['Deaths'], errors='coerce').fillna(0)
    df['Damage_Millions'] = pd.to_numeric(df['Damage_Millions'], errors='coerce').fillna(0)
    df.dropna(subset=['Latitude', 'Longitude', 'Country'], inplace=True)
    return df

def get_map_figure(df):
    df_map = df.copy()
    df_map['VEI_Size'] = df_map['VEI'].fillna(0.5)

    fig = px.scatter_geo(
        df_map,
        lat="Latitude",
        lon="Longitude",
        color="Type",
        size="VEI_Size",
        hover_name="Name",
        hover_data={"Country": True, "Year": True, "Deaths": True, "VEI_Size": False},
        title="Global Volcano Distribution",
        projection="natural earth",
        size_max=15,
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        margin={"r":0,"t":50,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    return fig

def get_frequency_figure(df):
    fig = px.histogram(
        df, 
        x="Year", 
        title="Eruption Frequency",
        nbins=100,
        template="plotly_dark"
    )
    fig.update_traces(marker_color='#ff5722')
    fig.update_layout(
        xaxis_title="Year", 
        yaxis_title="Count",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    return fig

def get_impact_figure(df):
    top_deadly = df.nlargest(10, 'Deaths').sort_values('Deaths', ascending=True)
    fig = px.bar(
        top_deadly,
        x="Deaths",
        y="Name",
        orientation='h',
        text="Deaths",
        title="Top 10 Deadliest Eruptions",
        template="plotly_dark"
    )
    fig.update_traces(marker_color='#ff5722', textposition='outside')
    fig.update_layout(
        xaxis_title="Deaths", 
        yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    return fig

def get_vei_analysis_figure(df, metric='median'):
    """
    Analysis 1: VEI vs Impact.
    Allows switching between Median, Mean, Total Deaths, and Total Eruptions.
    """
    # Map metric to pandas function and label
    metric_map = {
        'median': ('median', 'Median Deaths'),
        'mean': ('mean', 'Average Deaths'),
        'sum': ('sum', 'Total Deaths'),
        'count': ('count', 'Total Eruptions')
    }
    
    agg_func, label = metric_map.get(metric, ('median', 'Median Deaths'))
    
    # Group and Aggregate
    if metric == 'count':
        # For count, we just count the rows (occurrences of VEI)
        # We name the count column 'Total_Deaths' just to reuse the same y-axis reference in px.bar below
        df_vei = df.groupby('VEI').size().reset_index(name='Total_Deaths') 
    else:
        # We use 'Total_Deaths' as the target variable for death metrics
        df_vei = df.groupby('VEI')['Total_Deaths'].agg(agg_func).reset_index()
    
    fig = px.bar(
        df_vei, x="VEI", y="Total_Deaths",
        title=f"{label} by VEI",
        template="plotly_dark"
    )
    fig.update_traces(marker_color='#ff5722')
    fig.update_layout(
        xaxis_title="Volcanic Explosivity Index (VEI)",
        yaxis_title=label,
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="white"),
        height=400,
        autosize=False
    )
    return fig


def get_top_countries_by_historical_deaths_figure(df):
    # Analysis 2: Geographic Risk (Top 10 Countries by Total Deaths)
    df_country = df.groupby('Country')['Total_Deaths'].sum().nlargest(10).sort_values(ascending=True).reset_index()
    fig = px.bar(
        df_country, x="Total_Deaths", y="Country", orientation='h',
        title="Top 10 Countries by Historical Fatalities",
        template="plotly_dark"
    )
    fig.update_traces(marker_color='#ff5722')
    fig.update_layout(
        xaxis_title="Total Confirmed Deaths",
        yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="white")
    )
    return fig

def get_with_and_without_indirect_deaths_by_type_figure(df, metric='mean'):
    # Analysis 3: Secondary Hazards Impact
    # Compares lethality of events with vs. without Tsunami/Earthquake
    
    # Define aggregation logic
    if metric == 'sum_secondary':
        agg_func = 'sum'
        y_label = 'Total Deaths (Secondary Hazards Only)'
        # Filter for events with Tsunami OR Earthquake
        # This changes the baseline ("Without") to be "Other Secondary Hazards" instead of "All Other Events"
        df_to_use = df[df['Tsu'].notna() | df['Eq'].notna()].copy()
    else:
        metric_map = {
            'mean': 'mean',
            'median': 'median',
            'sum': 'sum'
        }
        agg_func = metric_map.get(metric, 'mean')
        df_to_use = df.copy()
        
        label_map = {
            'mean': 'Average Deaths',
            'median': 'Median Deaths',
            'sum': 'Total Deaths (All Eruptions)'
        }
        y_label = label_map.get(metric, 'Average Deaths')

    res = []
    
    # Tsunami Analysis
    tsu_yes = df_to_use[df_to_use['Tsu'].notna()]['Total_Deaths'].agg(agg_func)
    tsu_no = df_to_use[df_to_use['Tsu'].isna()]['Total_Deaths'].agg(agg_func)
    
    res.append({'Hazard': 'Tsunami', 'Status': 'With', 'Value': tsu_yes})
    res.append({'Hazard': 'Tsunami', 'Status': 'Without', 'Value': tsu_no})
    
    # Earthquake Analysis
    eq_yes = df_to_use[df_to_use['Eq'].notna()]['Total_Deaths'].agg(agg_func)
    eq_no = df_to_use[df_to_use['Eq'].isna()]['Total_Deaths'].agg(agg_func)
    
    res.append({'Hazard': 'Earthquake', 'Status': 'With', 'Value': eq_yes})
    res.append({'Hazard': 'Earthquake', 'Status': 'Without', 'Value': eq_no})
    
    df_hazards = pd.DataFrame(res)
    
    fig = px.bar(
        df_hazards, x="Hazard", y="Value", color="Status", barmode="group",
        title=f"Impact Amplification by Secondary Hazards ({y_label})",
        template="plotly_dark",
        color_discrete_map={'With': '#ff5722', 'Without': '#757575'}
    )
    fig.update_layout(
        yaxis_title=y_label,
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="white")
    )
    return fig

def get_volcano_type_figure(df, chart_type='treemap'):
    """
    Indicator 4: Volcanic Type vs Impact (Total Deaths).
    Allows the user to switch between a Treemap and a Bar Plot.
    """
    # 1. Prepare Data
    if df.empty:
        # Use go.Figure for consistent return type
        fig = go.Figure()
        fig.add_annotation(text="No Data Available", x=0.5, y=0.5, showarrow=False, font=dict(color="white"))
        return fig
        
    df_type = df.groupby('Type')['Total_Deaths'].sum().reset_index()
    # Ensure there are fatalities to plot
    df_type = df_type[df_type['Total_Deaths'] > 0] 
    
    if df_type.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Fatalities recorded in selection", x=0.5, y=0.5, showarrow=False, font=dict(color="white"))
        return fig

    # 2. Generate Figure based on type
    title_text = "Total Deaths by Volcano Type"
    
    if chart_type == 'bar':
        # Generate Horizontal Bar Plot (Easier to read long type names)
        fig = px.bar(
            df_type.sort_values('Total_Deaths', ascending=True), # Sort ascending for better visual hierarchy
            x='Total_Deaths', 
            y='Type', 
            orientation='h',
            title=title_text,
            template="plotly_dark"
        )
        fig.update_traces(marker_color='#ff5722')
        fig.update_xaxes(title_text="Total Deaths")
        fig.update_yaxes(title_text="")
        
    else: # Default is 'treemap'
        fig = px.treemap(
            df_type, path=['Type'], values='Total_Deaths',
            title=title_text,
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        # Treemap needs specific styling to hide labels
        fig.update_layout(uniformtext=dict(minsize=10, mode='hide')) 
    
    # 3. Apply Common Styling (to match dashboard theme)
    fig.update_layout(
        # Set height to stop infinite resizing loop if a row flexes height
        # Set a fixed height that looks good in the 2x2 grid layout
        height=400, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=40, b=10),
        
        # *** CRITICAL FIX FOR RESIZING LOOP ***
        # Explicitly set autosize to False and let Dash manage the dimensions
        # This often stops the resize-recalculate-resize loop
        autosize=False 
    )
    
    return fig

def volcano_type_vs_hasard_heatmap(df, normalize=False):

    # 1. Prepare Data for Heatmap
    # Assuming 'Agent' column contains comma-separated values that need to be exploded
    if 'Agent' not in df.columns or df['Agent'].dropna().empty:
            # Return a stylized "No Data" message instead of a blank plot
            fig = go.Figure()
            fig.add_annotation(
                text="No Hazard Data Available<br>for this selection",
                x=0.5, y=0.5, showarrow=False, 
                font=dict(size=20, color="gray")
            )
            fig.update_layout(
                template="plotly_dark",
                xaxis={'visible': False},
                yaxis={'visible': False},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            return fig

    df_agents = df.dropna(subset=['Agent']).copy()
    df_agents['Agent_List'] = df_agents['Agent'].apply(lambda x: [agent.strip() for agent in str(x).split(',') if agent.strip()])
    agent_exploded = df_agents.explode('Agent_List')
    agent_exploded.rename(columns={'Agent_List': 'Agent_Name'}, inplace=True)

    # Ensure 'Type' column is present for crosstab
    if 'Type' not in agent_exploded.columns:
        return px.scatter().update_layout(title="No Type Data Available", template="plotly_dark")

    agent_type_matrix = pd.crosstab(agent_exploded['Type'], agent_exploded['Agent_Name'])

    # Logic for Normalization
    if normalize:
        # Calculate total events per volcano type (using the full filtered df)
        total_events_by_type = df.groupby('Type').size()
        
        # Align indices: ensure we divide by the count of the correct type
        # We only care about types present in the matrix
        total_events_aligned = total_events_by_type.reindex(agent_type_matrix.index)
        
        # Divide and multiply by 100 for percentage
        # axis=0 means divide each column by the index (row) series
        agent_type_matrix = agent_type_matrix.div(total_events_aligned, axis=0) * 100
        
        title_text = "Heatmap: Risk Percentage (Hazard Probability per Eruption)"
        color_label = "Probability (%)"
        z_format = ".1f"
    else:
        title_text = "Heatmap: Volcano Types vs. Hazards (Agents)"
        color_label = "Count"
        z_format = "d"

    # 2. Create Plotly Heatmap
    fig = px.imshow(
        agent_type_matrix,
        x=agent_type_matrix.columns,
        y=agent_type_matrix.index,
        color_continuous_scale="Reds",
        title=title_text,
        template="plotly_dark",
        labels=dict(x="Hazard Agent", y="Volcano Type", color=color_label)
    )

    # Update hover template to show nice numbers
    fig.update_traces(hovertemplate="Type: %{y}<br>Agent: %{x}<br>" + color_label + ": %{z:" + z_format + "}<extra></extra>")

    # 3. Apply Common Styling (to match dashboard theme)
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=40, b=10),
        autosize=False,
        xaxis_title="Hazard Agent",
        yaxis_title="Volcano Type"
    )
    fig.update_xaxes(side="top")
    return fig

def get_type_vs_frequency(df):
# 1. Prepare Data
    type_stats = df.groupby('Type').agg({'Name': 'count', 'Deaths': 'mean'}).reset_index()
    type_stats.columns = ['Type', 'Count', 'Avg_Deaths']
    type_stats = type_stats[type_stats['Count'] > 1] # Remove singletons
    type_stats['Avg_Deaths'] = type_stats['Avg_Deaths'].fillna(0)
    
    # 2. Logic: Who gets a label?
    # We label the Top 3 by Frequency AND Top 3 by Deadliness
    top_freq = type_stats.nlargest(3, 'Count')['Type'].tolist()
    top_dead = type_stats.nlargest(3, 'Avg_Deaths')['Type'].tolist()
    # Combine unique labels to show
    labels_to_show = list(set(top_freq + top_dead))

    # Create a new column just for labels (others get empty string)
    type_stats['Label'] = type_stats.apply(
        lambda x: x['Type'] if x['Type'] in labels_to_show else "", axis=1
    )

    # 3. Create Plot
    fig = px.scatter(
        type_stats,
        x='Count',
        y='Avg_Deaths',
        size='Count',                # Bubble size = Frequency
        color='Avg_Deaths',          # Color = Danger
        text='Label',                # Use our smart label column
        color_continuous_scale='Reds',
        log_x=True,
        log_y=True,
        title='<b>Volcano Risk Matrix</b>: Frequency vs. Deadliness',
        labels={'Count': 'Frequency (Log Scale)', 'Avg_Deaths': 'Avg. Deaths (Log Scale)'},
        template="plotly_dark"
    )

    # 4. Add Quadrant Lines (The "Crosshairs")
    # We use x=20 and y=100 as visual thresholds for "High Freq" and "High Death"
    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=20, line_dash="dash", line_color="gray", opacity=0.5)

    # 5. Add Context Annotations (The "Story")
    fig.add_annotation(x=np.log10(500), y=np.log10(2000), text="<b>CRITICAL THREATS</b><br>(Frequent & Deadly)", 
                       showarrow=False, font=dict(color="red", size=10))
    fig.add_annotation(x=np.log10(3), y=np.log10(2000), text="<b>BLACK SWANS</b><br>(Rare but Catastrophic)", 
                       showarrow=False, font=dict(color="orange", size=10))

    # 6. Styling Polish
    fig.update_traces(
        textposition='top center', # Move text above dot
        marker=dict(line=dict(width=1, color='White')) # Add white ring to dots for contrast
    )
    
    fig.update_traces(marker=dict(color='#ff5722', opacity=0.7))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        showlegend=False,
        coloraxis_showscale=False,
        font=dict(family="Arial", size=12)
    )

    return fig

def get_deaths_vs_damage_figure(df):
    """
    Scatter plot of Deaths vs Damage.
    Low availability (~18 events, treat as anecdotal).
    """
    # Filter zeros
    df_plot = df[(df['Deaths'] != 0) & (df['Damage_Millions'] != 0)].copy()
    
    fig = px.scatter(
        df_plot, x="Deaths", y="Damage_Millions",
        title="Deaths vs. Damage ($M)",
        template="plotly_dark",
        hover_name="Name",
        hover_data=["Country", "Year"]
    )
    fig.update_traces(marker=dict(color='#ff5722', opacity=0.7))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="white")
    )
    return fig

def get_elevation_vs_vei_figure(df):
    """
    Scatter plot of Elevation vs VEI.
    Full availability (Good for debunking myths).
    """
    # Filter zeros
    df_plot = df[df['Elevation'] != 0].copy()

    fig = px.scatter(
        df_plot, x="VEI", y="Elevation",
        title="Elevation vs. VEI",
        template="plotly_dark",
        hover_name="Name",
        hover_data=["Country", "Year"]
    )
    fig.update_traces(marker=dict(color='#ff5722', opacity=0.7))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="white")
    )
    return fig

# Initialize App
app = Dash(__name__)

# Load Data
df = load_data()

# Styles
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#111111",
    "color": "white"
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#000000",
    "min-height": "100vh",
    "color": "white"
}

CARD_STYLE = {
    "background-color": "#1e1e1e",
    "padding": "20px",
    "border-radius": "10px",
    "margin-bottom": "20px",
    "box-shadow": "0 4px 6px rgba(0,0,0,0.3)"
}

# Layout
app.layout = html.Div([
    # Sidebar
    html.Div([
        html.H2("Volcano Insights", style={'font-size': '20px', 'margin-bottom': '20px', 'color': '#ff5722'}),
        html.Hr(style={'border-color': '#333'}),
        html.P("Filters", style={'color': '#888'}),
        
        html.Label("Year Range", style={'margin-top': '20px'}),
        dcc.RangeSlider(
            id='year-slider',
            min=df['Year'].min(),
            max=df['Year'].max(),
            value=[df['Year'].min(), df['Year'].max()],
            marks={str(year): str(year) for year in range(int(df['Year'].min()), int(df['Year'].max()), 1000)},
            tooltip={"placement": "bottom", "always_visible": True},
            className="dark-slider"
        ),
        
        html.Label("Country", style={'margin-top': '20px'}),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': c, 'value': c} for c in sorted(df['Country'].unique())],
            placeholder="All Countries",
            style={'color': 'black'} # Dropdown text needs to be black to be visible on white bg of default dropdown
        )
    ], style=SIDEBAR_STYLE),

    # Main Content
    html.Div([
        html.H1("Volcano Insights Dashboard", style={'margin-bottom': '5px'}),
        html.P("Analyzing Significant Volcanic Eruptions", style={'color': '#888', 'margin-bottom': '30px'}),

        # KPI Row
        html.Div([
            html.Div([
                html.H4("Total Eruptions", style={'color': '#888', 'font-size': '14px'}),
                html.H2(id='kpi-eruptions', style={'font-size': '32px'})
            ], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
            html.Div([
                html.H4("Total Deaths", style={'color': '#888', 'font-size': '14px'}),
                html.H2(id='kpi-deaths', style={'font-size': '32px'})
            ], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
            html.Div([
                html.H4("Total Damage ($M)", style={'color': '#888', 'font-size': '14px'}),
                html.H2(id='kpi-damage', style={'font-size': '32px'})
            ], style={**CARD_STYLE, 'flex': '1'})
        ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '20px'}),

        # Charts Row 1
        html.Div([
            html.Div([dcc.Graph(id='map-graph')], style={**CARD_STYLE, 'flex': '2', 'margin-right': '20px'}),
            html.Div([dcc.Graph(id='time-graph')], style={**CARD_STYLE, 'flex': '1'})
        ], style={'display': 'flex', 'margin-bottom': '20px'}),

        # Charts Row 2 - impact charts
        html.Div([
            html.Div([dcc.Graph(id='impact-graph')], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
        ], style={'display': 'flex'}),

        # Correlation charts
        # Correlation chart row 1
        html.Div([
            html.Div([
                # New Control: Radio Buttons for VEI Metric
                html.Div([
                    dcc.RadioItems(
                        id='vei-metric-selector',
                        options=[
                            {'label': ' Median Deaths', 'value': 'median'},
                            {'label': ' Mean Deaths', 'value': 'mean'},
                            {'label': ' Total Deaths', 'value': 'sum'},
                            {'label': ' Total Eruptions', 'value': 'count'}
                        ],
                        value='median', # Default view
                        labelStyle={'display': 'inline-block', 'margin-right': '20px'},
                        style={'color': 'white', 'marginBottom': '10px'}
                    ),
                ], style={'textAlign': 'center'}),
                
                dcc.Graph(id='median_deaths_by_VIE', style={'height': '400px'})
            ], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
            
            html.Div([dcc.Graph(id='top_countries_by_historical_deaths', style={'height': '400px'})], style={**CARD_STYLE, 'flex': '1'})
        ], style={'display': 'flex'}),
        
        # Correlation chart row 2
        html.Div([
                html.Div([
                    html.Div([
                        dcc.RadioItems(
                            id='secondary-hazard-metric',
                            options=[
                                {'label': ' Median Deaths', 'value': 'median'},
                                {'label': ' Mean Deaths', 'value': 'mean'},
                                {'label': ' Total Deaths (All Eruptions)', 'value': 'sum'},
                                {'label': ' Total Deaths (Secondary Hazards Only)', 'value': 'sum_secondary'}
                            ],
                            value='mean',
                            labelStyle={'display': 'inline-block', 'margin-right': '20px'},
                            style={'color': 'white', 'marginBottom': '10px'}
                        ),
                    ], style={'textAlign': 'center'}),
                    dcc.Graph(id='with_and_without_indirect_deaths_by_type')
                ], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
                
                # --- START OF CHANGE ---
                html.Div([
                    # New Control: Radio Buttons for Chart Type
                    html.Div([
                        dcc.RadioItems(
                            id='volcano-type-selector',
                            options=[
                                {'label': ' Treemap View', 'value': 'treemap'},
                                {'label': ' Bar Plot View', 'value': 'bar'}
                            ],
                            value='treemap', # Default view
                            labelStyle={'display': 'inline-block', 'margin-right': '20px'},
                            style={'color': 'white', 'marginBottom': '10px'}
                        ),
                    ], style={'textAlign': 'center'}), 

                    # Chart Container
                    dcc.Graph(id='volcano_type'),
                    
                ], style={**CARD_STYLE, 'flex': '1'})
                
            ],),
            




        # New Graphs Row 1
        html.Div([
            html.Div([
                html.Div([
                    dcc.RadioItems(
                        id='heatmap-normalization-selector',
                        options=[
                            {'label': ' Count', 'value': 'count'},
                            {'label': ' Risk Percentage', 'value': 'percent'}
                        ],
                        value='count',
                        labelStyle={'display': 'inline-block', 'margin-right': '20px'},
                        style={'color': 'white', 'marginBottom': '10px', 'textAlign': 'center'}
                    )
                ]),
                # --- THE FIX IS HERE ---
                # You must define height in CSS because autosize is False in the figure
                dcc.Graph(id='vei-deaths-graph', style={'height': '400px', 'width': '100%'}) 
                
            ], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
            
            html.Div([dcc.Graph(id='deaths-injuries-graph')], style={**CARD_STYLE, 'flex': '1'})
        ], style={'display': 'flex', 'margin-bottom': '20px'}),

        # New Graphs Row 2
        html.Div([
            html.Div([dcc.Graph(id='deaths-damage-graph')], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
            html.Div([dcc.Graph(id='elevation-vei-graph')], style={**CARD_STYLE, 'flex': '1'})
        ], style={'display': 'flex'}),

    ], style=CONTENT_STYLE)
],style={'backgroundColor': '#000000', 'minHeight': '100vh'})

@app.callback(
    [Output('map-graph', 'figure'),
     Output('time-graph', 'figure'),
     Output('impact-graph', 'figure'),
     Output('median_deaths_by_VIE', 'figure'),
     Output('top_countries_by_historical_deaths', 'figure'),
     Output('with_and_without_indirect_deaths_by_type', 'figure'),
     Output('volcano_type', 'figure'),
     Output('vei-deaths-graph', 'figure'),
     Output('deaths-injuries-graph', 'figure'),
     Output('deaths-damage-graph', 'figure'),
     Output('elevation-vei-graph', 'figure'),
     Output('kpi-eruptions', 'children'),
     Output('kpi-deaths', 'children'),
     Output('kpi-damage', 'children')],
    [Input('country-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('volcano-type-selector', 'value'),
     # ADDED INPUT: The selector for the VEI chart
     Input('vei-metric-selector', 'value'),
     Input('secondary-hazard-metric', 'value'),
     Input('heatmap-normalization-selector', 'value')] 
)
def update_dashboard(selected_country, year_range, selected_chart_type, selected_vei_metric, selected_secondary_metric, selected_heatmap_metric):
    # Filter Data
    dff = df.copy()
    if selected_country:
        dff = dff[dff['Country'] == selected_country]
    
    if year_range:
        dff = dff[(dff['Year'] >= year_range[0]) & (dff['Year'] <= year_range[1])]

    if dff.empty:
        dff = df # Fallback if empty

    # KPIs
    total_eruptions = len(dff)
    total_deaths = f"{int(dff['Deaths'].sum()):,}"
    total_damage = f"${dff['Damage_Millions'].sum():,.0f}"

    # Figures
    fig1 = get_map_figure(dff)
    fig2 = get_frequency_figure(dff)
    fig3 = get_impact_figure(dff)
    
    # MODIFIED: Pass the new selector value to the VEI function
    fig_vei = get_vei_analysis_figure(dff, selected_vei_metric)
    
    fig_top_countries = get_top_countries_by_historical_deaths_figure(dff)
    fig_indirect = get_with_and_without_indirect_deaths_by_type_figure(dff, selected_secondary_metric)
    fig_volcano_type = get_volcano_type_figure(dff, selected_chart_type)
    
    # New Graphs
    fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=(selected_heatmap_metric == 'percent'))
    fig_deaths_injuries = get_type_vs_frequency(dff)
    fig_deaths_damage = get_deaths_vs_damage_figure(dff)
    fig_elevation_vei = get_elevation_vs_vei_figure(dff)
    
    return fig1, fig2, fig3, fig_vei, fig_top_countries, fig_indirect, fig_volcano_type, fig_vei_deaths, fig_deaths_injuries, fig_deaths_damage, fig_elevation_vei, total_eruptions, total_deaths, total_damage

if __name__ == '__main__':
    print("Launching Dashboard...")
    print("Dashboard launched at: http://127.0.0.1:8051")
    app.run(host='127.0.0.1', port=8051, debug=True)
