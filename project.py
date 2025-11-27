import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

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

def get_with_and_without_indirect_deaths_by_type_figure(df):
    # Analysis 3: Secondary Hazards Impact
    # Compares average lethality of events with vs. without Tsunami/Earthquake
    res = []
    
    # Tsunami Analysis
    tsu_yes = df[df['Tsu'].notna()]['Total_Deaths'].mean()
    tsu_no = df[df['Tsu'].isna()]['Total_Deaths'].mean()
    res.append({'Hazard': 'Tsunami', 'Status': 'With', 'Avg_Deaths': tsu_yes})
    res.append({'Hazard': 'Tsunami', 'Status': 'Without', 'Avg_Deaths': tsu_no})
    
    # Earthquake Analysis
    eq_yes = df[df['Eq'].notna()]['Total_Deaths'].mean()
    eq_no = df[df['Eq'].isna()]['Total_Deaths'].mean()
    res.append({'Hazard': 'Earthquake', 'Status': 'With', 'Avg_Deaths': eq_yes})
    res.append({'Hazard': 'Earthquake', 'Status': 'Without', 'Avg_Deaths': eq_no})
    
    df_hazards = pd.DataFrame(res)
    
    fig = px.bar(
        df_hazards, x="Hazard", y="Avg_Deaths", color="Status", barmode="group",
        title="Impact Amplification by Secondary Hazards",
        template="plotly_dark",
        color_discrete_map={'With': '#ff5722', 'Without': '#757575'}
    )
    fig.update_layout(
        yaxis_title="Average Deaths per Event",
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
                html.Div([dcc.Graph(id='with_and_without_indirect_deaths_by_type')], style={**CARD_STYLE, 'flex': '1', 'margin-right': '20px'}),
                
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
                # --- END OF CHANGE ---
                
            ],)

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
     Output('kpi-eruptions', 'children'),
     Output('kpi-deaths', 'children'),
     Output('kpi-damage', 'children')],
    [Input('country-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('volcano-type-selector', 'value'),
     # ADDED INPUT: The selector for the VEI chart
     Input('vei-metric-selector', 'value')] 
)
def update_dashboard(selected_country, year_range, selected_chart_type, selected_vei_metric):
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
    fig_indirect = get_with_and_without_indirect_deaths_by_type_figure(dff)
    fig_volcano_type = get_volcano_type_figure(dff, selected_chart_type)
    
    return fig1, fig2, fig3, fig_vei, fig_top_countries, fig_indirect, fig_volcano_type, total_eruptions, total_deaths, total_damage

if __name__ == '__main__':
    print("Launching Dashboard...")
    print("Dashboard launched at: http://127.0.0.1:7860")
    app.run(host='127.0.0.1', port=7860, debug=True)
