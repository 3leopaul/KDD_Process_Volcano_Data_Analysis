import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, ctx, dash_table
import plotly.graph_objects as go
import numpy as np
import src.components.impact_analysis as impact
from prophet import Prophet


def load_raw_data(filepath):
    """
    Reads the TSV file.
    Input: filepath (str)
    Output: raw dataframe (pd.DataFrame)
    """
    try:
        df = pd.read_csv(filepath, sep='\t')
        print("File loaded.")
        return df
    except FileNotFoundError:
        print("File not found. Please check the path.")
        return None

def clean_data(df):
    """
    Applies preprocessing: renaming columns, handling types, and filling NaNs.
    Input: df (pd.DataFrame) : The raw dataframe
    Output: df (pd.DataFrame) : The cleaned dataframe
    """
    #Rename columns to remove spaces and special characters for easier coding 
    #and for a better understanding
    df = df.rename(columns={
        'Mo': 'Month',
        'Dy': 'Day',
        'Tsu': 'Tsunami',
        'Eq': 'Earthquake',
        'Damage ($Mil)': 'Damage_Millions',
        'Total Damage ($Mil)': 'Total_Damage_Millions',
        'Elevation (m)': 'Elevation',
        'Total Deaths': 'Total_Deaths',
        'Total Injuries': 'Total_Injuries'
    })

    #If 'Deaths' is empty, we assume 0 for the sake of calculation, rather than dropping the row.
    cols_to_fix = ['VEI', 'Deaths', 'Damage_Millions', 'Injuries']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    #We drop rows without Lat/Lon/Country because we cannot visualize them on a map.
    df = df.dropna(subset=['Latitude', 'Longitude', 'Country'])

    return df



def load_data(filepath="volcano-events.tsv"):
    df = load_raw_data(filepath)
    if df is None:
        return pd.DataFrame()

    df = clean_data(df)

    # Ensure Year is numeric and drop rows with missing Year (critical for slider)
    # This might be redundant if added to clean_data, but keeping it here for safety as per plan
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df.dropna(subset=['Year'], inplace=True)
    
    return df

# Function: Build a scatter-based world map showing individual volcano eruptions.
# Input:
#   - df (pd.DataFrame): filtered volcano dataset containing at least
#       ["Latitude", "Longitude", "Type", "Name", "VEI", "Country", "Year", "Deaths"]
# Output:
#   - fig (plotly.graph_objs.Figure): an interactive scatter_geo map (used in Dash)

def get_map_points(df):
    # Copy the dataframe to avoid modifying the original one
    df_map = df.copy()

    # Replace missing VEI values with a small default value (0.5)
    # to avoid invisible points on the map
    df_map['VEI_Size'] = df_map['VEI'].fillna(0.5)

    # Create the base geographic scatter plot
    fig = px.scatter_geo(
        df_map,
        lat="Latitude",           # latitude of volcano
        lon="Longitude",          # longitude of volcano
        color="Type",             # volcano morphological category
        size="VEI_Size",          # bubble size based on VEI (explosivity)
        hover_name="Name",        # volcano name in tooltip
        hover_data={              # additional tooltip information
            "Country": True,
            "Year": True,
            "Deaths": True,
            "VEI": True,
            "VEI_Size": False
        },
        title="Global Volcano Distribution (Bubble size = VEI)",
        projection="natural earth", # projection style
        size_max=15,                # maximum bubble size
        template="plotly_dark"      # dark theme to match dashboard
    )

    # Custom color palette: 20 vivid volcanic colors (orange → red → magenta → violet)
    warm_palette = [
   
    "#ffd500",  # deep orange
    "#ff8f00",  # vivid orange
    "#ff3d00",  # bright red-orange
    "#ff1a00",  # pure red-orange
    "#e60000",  # intense red
    "#c51162",  # magenta
    "#ff0055",  # neon pink-red
    "#d81b60",  # pink-magenta
    "#b0003a",  # dark magenta-red
    "#9c004d",  # deep pink-purple
    "#aa00ff",  # neon violet
    "#8e24aa",  # classic violet
    "#7b1fa2",  # deep violet
    "#6a1b9a",  # darker violet
    "#4a148c",  # almost purple-black
    "#7f0000",
    "#b30000",
    "#d50000",
    "#ff1744",
    "#ff4081"
    ]

    n_traces = len(fig.data)   # one trace per volcano Type
    n_colors = len(warm_palette)

    # Assign a distinct color from the palette to each volcano Type
    for i, trace in enumerate(fig.data):
        color = warm_palette[i % n_colors]     # loop through palette if Types > 20
        trace.marker.update(
            color=color,
            line=dict(width=0)                 # remove outline for cleaner look
        )

    # Add geographic features (coastlines, countries, land)
    fig.update_geos(
        showcountries=True,
        showcoastlines=True,
        showland=True,
    )

    # Transparent background to match the dashboard's dark theme
    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        legend=dict(itemdoubleclick=False)
    )

    return fig

# Function: Build a choropleth (colored world map) aggregated by country.
# Input:
#   - df (pd.DataFrame): filtered volcano dataset containing at least:
#       ["Country", value_col]
#   - value_col (str): column name used for coloring (e.g., "Count", "Deaths", "Damage_Millions")
#   - title (str): title of the choropleth
#   - color_label (str): label for the colorbar (e.g., "Eruptions", "Deaths", "Damage")
# Output:
#   - fig (plotly.graph_objs.Figure): an interactive choropleth map (used in Dash)

def get_country_choropleth(df, value_col, title, color_label):
    # Aggregate data by country for the selected metric (count, deaths, damage…)
    agg = df.groupby('Country', as_index=False)[value_col].sum()
    # Custom continuous volcanic colormap (dark red → orange → magenta → violet)
    # Designed to avoid white/yellow and emphasize bright volcanic tones
    volcano_scale = [
        (0.00, "#000000"),   # very dark base
        (0.05, "#4b0000"),   # deep red
        (0.10, "#7f0000"),   # darker red
        (0.20, "#b00000"),   # intense red
        (0.30, "#d50000"),   # bright red
        (0.40, "#ff1400"),   # red-orange (flashy)
        (0.55, "#ff3d00"),   # bright orange-red
        (0.70, "#ff6d00"),   # orange incandescent
        (0.85, "#ff8500"),   # bright orange
        (0.93, "#d81b60"),   # magenta
        (1.00, "#6a1b9a")    # deep violet
    ]
    # Build the choropleth map
    fig = px.choropleth(
        agg,
        locations='Country',            # country name column
        locationmode='country names',   # match names to world countries
        color=value_col,                # metric used for color intensity
        hover_name='Country',           # tooltip title
        title=title,
        labels={value_col: color_label}, # name of the color axis
        template="plotly_dark",          # dark theme
        color_continuous_scale=volcano_scale,
        projection="natural earth"       # projection style
    )
    # Display country borders, coastlines, and land
    fig.update_geos(
        showcountries=True,
        showcoastlines=True,
        showland=True
    )
    # Transparent background to blend with the dashboard
    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )

    return fig

def create_expanding_buttons(group_id, options, default_value):
    """
    Creates a group of expanding buttons with a dcc.Store for state management.
    """
    buttons = []
    for opt in options:
        value = opt['value']
        label = opt['label']
        is_active = (value == default_value)
        
        style = {
            'flex-grow': '3' if is_active else '1',
            'background-color': '#ff5722' if is_active else '#333',
            'color': 'white' if is_active else '#888',
            'padding': '10px',
            'margin-right': '5px',
            'border-radius': '5px',
            'cursor': 'pointer',
            'text-align': 'center',
            'overflow': 'hidden',
            'white-space': 'nowrap',
            'transition': 'all 0.5s ease'
        }
        
        # We use the label as the text. 
        # For inactive buttons, we might want a shorter version if provided, 
        # but for now we'll rely on the flex-grow to hide/show text or just let it clip?
        # The user requirement is "expend at the expense of the others to show the full name".
        # So inactive ones are small.
        
        buttons.append(html.Div(label, id=f'btn-{group_id}-{value}', n_clicks=0, style=style))

    return html.Div([
        dcc.Store(id=f'{group_id}-store', data=default_value),
        html.Div(buttons, style={'display': 'flex', 'width': '100%', 'justify-content': 'center', 'marginBottom': '10px'})
    ])


def build_eruptions_per_year(df):
    """
    Build a yearly time series: index = Year, value = number of eruptions.
    We drop missing or invalid (<= 0) years.
    """
    temp = df.dropna(subset=["Year"]).copy()
    temp = temp[temp["Year"] > 0]

    eruptions_per_year = (
        temp
        .groupby("Year")
        .size()
        .sort_index()
    )

    eruptions_per_year.index = eruptions_per_year.index.astype(int)
    eruptions_per_year.name = "eruptions_per_year"

    return eruptions_per_year

def aggregate_eruptions(df, by="year"):
    """
    Aggregate eruptions by year or by century.
    Returns a dataframe with two columns: period, count.
    """
    temp = df.dropna(subset=["Year"]).copy()
    temp = temp[temp["Year"] > 0]  # keep AD years only

    if by == "year":
        grouped = (
            temp.groupby("Year")
            .size()
            .reset_index(name="count")
        )
        grouped.rename(columns={"Year": "period"}, inplace=True)

    elif by == "century":
        # Century numbering: 1..n (e.g. 19 = 1801-1900)
        temp["century"] = ((temp["Year"] - 1) // 100 + 1).astype(int)
        grouped = (
            temp.groupby("century")
            .size()
            .reset_index(name="count")
        )
        grouped.rename(columns={"century": "period"}, inplace=True)

    else:
        raise ValueError("by must be 'year' or 'century'")

    return grouped

def render_time_series(df, by="year"):
    """
    Build a time-series figure of eruption frequency over time
    using Plotly Express, either per year or per century.
    """
    agg = aggregate_eruptions(df, by=by)

    if by == "year":
        x_label = "Year"
        title = "Number of eruptions per year"
    else:
        x_label = "Century"
        title = "Number of eruptions per century"

    fig = px.line(
        agg,
        x="period",
        y="count",
        markers=True,
        labels={"period": x_label, "count": "Number of eruptions"},
        title=title,
        color_discrete_sequence=['#ff5722']  # orange/red curve
    )

    fig.update_layout(
        height=320,
        autosize=False,
        paper_bgcolor='rgba(0,0,0,0)',   # transparent to fit the dark card
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        xaxis=dict(
            tickmode="auto",
            tickangle=-45
        ),
        margin=dict(l=50, r=20, t=60, b=40)
    )

    fig.update_traces(
        hovertemplate=f"{x_label}: %{{x}}<br>Eruptions: %{{y}}<extra></extra>"
    )

    return fig

def prepare_prophet_df(eruptions_per_year, min_year=1800):
    """
    Prepare data for Prophet:
    - Filter years >= min_year
    - Rename columns to 'ds' (date) and 'y' (value)
    - Convert Year to datetime
    """
    df_p = eruptions_per_year[eruptions_per_year.index >= min_year].reset_index()
    df_p.columns = ["Year", "y"]
    df_p["ds"] = pd.to_datetime(df_p["Year"], format="%Y")
    return df_p

def forecast_eruptions(df_prophet, n_future_years=20):
    """
    Fit a Prophet model on the historical data and forecast n_future_years ahead.
    """
    model = Prophet()
    model.fit(df_prophet)

    # Generate future dates (one point per year)
    future_dates = model.make_future_dataframe(periods=n_future_years, freq="YE")

    # Predict on both historical + future dates
    prediction = model.predict(future_dates)

    return prediction

def make_forecast_figure(df_prophet, prediction):
    """
    Build a Plotly figure showing historical yearly eruptions
    and Prophet forecast.
    """
    fig = go.Figure()

    # Historical data
    fig.add_trace(go.Scatter(
        x=df_prophet["ds"],
        y=df_prophet["y"],
        mode="lines",
        name="Historical",
        line=dict(color="#ff5722", width=2)
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=prediction["ds"],
        y=prediction["yhat"],
        mode="lines",
        name="Forecast",
        line=dict(color="#ff9800", width=2, dash="dash")  # orange, dashed
    ))

    fig.update_layout(
        title="Forecast of volcanic eruptions per year (Prophet)",
        xaxis_title="Year",
        yaxis_title="Number of eruptions",
        height=320,
        paper_bgcolor='rgba(0,0,0,0)',   # same as other cards
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=50, r=20, t=60, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )

    return fig

def make_empty_forecast_figure(message):
    """
    Simple empty figure used when there is not enough data
    to fit a reliable Prophet model (e.g. after filters).
    """
    fig = go.Figure()
    fig.update_layout(
        title=message,
        xaxis_title="Time",
        yaxis_title="Number of eruptions",
        height=320,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=50, r=20, t=60, b=40)
    )
    return fig


def render_temporal_series(df, mode="year"):
    """
    3 modes for the dashboard:
    - 'year'    : time series per year (uses render_time_series)
    - 'century' : time series per century (uses render_time_series)
    - 'smooth'  : yearly series + 10-year moving average (Plotly)
    """
    # 1) Yearly series (raw)
    if mode == "year":
        return render_time_series(df, by="year")

    # 2) Century series (raw)
    if mode == "century":
        return render_time_series(df, by="century")

    # 3) Smoothed yearly series (10-year moving average)
    if mode == "smooth":
        per_year = build_eruptions_per_year(df)
        smooth = per_year.rolling(window=10).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=per_year.index,
            y=per_year.values,
            mode="lines",
            name="Raw yearly data",
            line=dict(width=1, color="#888")   # grey, less dominant
        ))
        fig.add_trace(go.Scatter(
            x=smooth.index,
            y=smooth.values,
            mode="lines",
            name="10-year moving average",
            line=dict(width=3, color="#ff5722")  # main orange/red curve
        ))

        fig.update_layout(
            title="Smoothed eruptions per year (10-year moving average)",
            xaxis_title="Year",
            yaxis_title="Number of eruptions",
            height=320,
            autosize=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=50, r=20, t=60, b=40)
        )
        return fig

    # 4) Prophet Forecast
    if mode == "forecast":
        eruptions_per_year = build_eruptions_per_year(df)
        # We need enough data points
        if len(eruptions_per_year) < 20:
            return make_empty_forecast_figure("Not enough data for forecast (need >20 years)")
        
        try:
            df_prophet = prepare_prophet_df(eruptions_per_year, min_year=1800)
            if len(df_prophet) < 10:
                 return make_empty_forecast_figure("Not enough data since 1800 for forecast")
                 
            prediction = forecast_eruptions(df_prophet, n_future_years=50)
            return make_forecast_figure(df_prophet, prediction)
        except Exception as e:
            return make_empty_forecast_figure(f"Forecast Error: {str(e)}")
            
    return go.Figure()

def get_impact_figure(df):
    top_deadly = df.nlargest(10, 'Deaths').sort_values('Deaths', ascending=True).copy()
    
    def format_label(row):
        y = row['Year']
        try:
            y_int = int(y)
            suffix = "BC" if y_int < 0 else "AD"
            return f"{row['Name']} ({abs(y_int)} {suffix})"
        except:
            return f"{row['Name']} ({y})"

    top_deadly['Label'] = top_deadly.apply(format_label, axis=1)
    
    fig = px.bar(
        top_deadly,
        x="Deaths",
        y="Label",
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
    # Check if we are analyzing Agents or Secondary Hazards
    is_agent_analysis = metric.endswith('_agents')
    
    # Clean metric name for mapping
    base_metric = metric.replace('_agents', '')
    
    metric_map = {
        'mean': 'mean',
        'median': 'median',
        'sum': 'sum'
    }
    agg_func = metric_map.get(base_metric, 'mean')
    df_to_use = df.copy()
    
    label_map = {
        'mean': 'Average Deaths',
        'median': 'Median Deaths',
        'sum': 'Total Deaths (All Eruptions)'
    }
    y_label = label_map.get(base_metric, 'Average Deaths')
    
    res = []

    if is_agent_analysis:
        # Analyze All Agents
        agents_to_analyze = [
            ('P', 'Pyroclastic Flow'),
            ('M', 'Mudflow (Lahar)'),
            ('T', 'Tephra (Ash)'),
            ('W', 'Waves (Tsunami)'),
            ('L', 'Lava Flow'),
            ('G', 'Gas'),
            ('I', 'Indirect'),
            ('A', 'Avalanche'),
            ('F', 'Floods'),
            ('S', 'Seismic'),
            ('E', 'Electrical'),
            ('m', 'Mudflow (Lahar) (m)'),
            ('?', 'Unknown')
        ]
        title_suffix = "(Agents)"
        
        for code, name in agents_to_analyze:
            # Check if Agent column contains the code
            mask = df_to_use['Agent'].astype(str).apply(lambda x: code in [a.strip() for a in x.split(',')])
            
            val_yes = df_to_use[mask]['Total_Deaths'].agg(agg_func)
            val_no = df_to_use[~mask]['Total_Deaths'].agg(agg_func)
            
            res.append({'Hazard': name, 'Status': 'With', 'Value': val_yes})
            res.append({'Hazard': name, 'Status': 'Without', 'Value': val_no})
            
    else:
        # Analyze Secondary Hazards: Tsunami, Earthquake
        title_suffix = "(Secondary Hazards)"
        
        # Tsunami Analysis
        tsu_yes = df_to_use[df_to_use['Tsunami'].notna()]['Total_Deaths'].agg(agg_func)
        tsu_no = df_to_use[df_to_use['Tsunami'].isna()]['Total_Deaths'].agg(agg_func)
        res.append({'Hazard': 'Tsunami', 'Status': 'With', 'Value': tsu_yes})
        res.append({'Hazard': 'Tsunami', 'Status': 'Without', 'Value': tsu_no})

        # Earthquake Analysis
        eq_yes = df_to_use[df_to_use['Earthquake'].notna()]['Total_Deaths'].agg(agg_func)
        eq_no = df_to_use[df_to_use['Earthquake'].isna()]['Total_Deaths'].agg(agg_func)
        res.append({'Hazard': 'Earthquake', 'Status': 'With', 'Value': eq_yes})
        res.append({'Hazard': 'Earthquake', 'Status': 'Without', 'Value': eq_no})

    df_hazards = pd.DataFrame(res)
    
    fig = px.bar(
        df_hazards, x="Hazard", y="Value", color="Status", barmode="group",
        title=f"Impact Amplification by {title_suffix} ({y_label})",
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

def get_volcano_type_figure(df, scale='log', metric='total'):
    """
    Indicator 4: Volcanic Type vs Impact.
    Displays Total Deaths or Deaths per Eruption by Volcano Type with selectable scale.
    """
    # 1. Prepare Data
    if df.empty:
        # Use go.Figure for consistent return type
        fig = go.Figure()
        fig.add_annotation(text="No Data Available", x=0.5, y=0.5, showarrow=False, font=dict(color="white"))
        return fig
        
    # Group by Type and calculate sums and counts
    df_type = df.groupby('Type').agg(
        Total_Deaths=('Total_Deaths', 'sum'),
        Count=('Name', 'count')
    ).reset_index()
    
    # Calculate Rate
    df_type['Deaths_per_Eruption'] = df_type['Total_Deaths'] / df_type['Count']
    
    # Filter out 0s for the plot to avoid log scale issues or clutter
    # For 'total', we filter Total_Deaths > 0
    # For 'rate', we also want Total_Deaths > 0 (implies rate > 0)
    df_type = df_type[df_type['Total_Deaths'] > 0] 
    
    if df_type.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Fatalities recorded in selection", x=0.5, y=0.5, showarrow=False, font=dict(color="white"))
        return fig

    # 2. Generate Figure
    is_log = (scale == 'log')
    
    if metric == 'rate':
        x_col = 'Deaths_per_Eruption'
        title_text = "Deaths per Eruption by Volcano Type"
        x_axis_label = f"Deaths per Eruption ({'Log' if is_log else 'Linear'} Scale)"
        hover_template = "Type: %{y}<br>Deaths/Eruption: %{x:.2f}<extra></extra>"
    else:
        x_col = 'Total_Deaths'
        title_text = "Total Deaths by Volcano Type"
        x_axis_label = f"Total Deaths ({'Log' if is_log else 'Linear'} Scale)"
        hover_template = "Type: %{y}<br>Total Deaths: %{x}<extra></extra>"

    
    # Generate Horizontal Bar Plot
    fig = px.bar(
        df_type.sort_values(x_col, ascending=True), 
        x=x_col, 
        y='Type', 
        orientation='h',
        title=title_text,
        template="plotly_dark",
        log_x=is_log
    )
    fig.update_traces(marker_color='#ff5722', hovertemplate=hover_template)
    fig.update_xaxes(title_text=x_axis_label)
    fig.update_yaxes(title_text="")
    
    # 3. Apply Common Styling (to match dashboard theme)
    fig.update_layout(
        height=400, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=40, b=10),
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
    
    # Map codes to full names
    hazard_map = {
        'P': 'Pyroclastic Flow',
        'M': 'Mudflow (Lahar)',
        'T': 'Tephra (Ash)',
        'W': 'Waves (Tsunami)',
        'L': 'Lava Flow',
        'G': 'Gas',
        'I': 'Indirect',
        'A': 'Avalanche',
        'F': 'Floods',
        'S': 'Seismic',
        'E': 'Electrical',
        'm': 'Mudflow (Lahar)',
        '?': 'Unknown'
    }
    agent_exploded['Agent_Name'] = agent_exploded['Agent_List'].map(hazard_map).fillna(agent_exploded['Agent_List'])

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
        labels=dict(x="Hazard Agent", y="Volcano Type", color=color_label),
        aspect="auto"
    )

    # Update hover template to show nice numbers
    fig.update_traces(hovertemplate="Type: %{y}<br>Agent: %{x}<br>" + color_label + ": %{z:" + z_format + "}<extra></extra>")

    # 3. Apply Common Styling (to match dashboard theme)
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=40, b=80), # Increased bottom margin for diagonal labels
        autosize=True,
        xaxis_title="Hazard Agent",
        yaxis_title="Volcano Type"
    )
    fig.update_xaxes(side="bottom", tickangle=-45)
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
        marker=dict(line=dict(width=1, color='White'), sizemin=5) # Add white ring and min size
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

def get_volcano_type_stats_table(df):
    """
    Creates a table showing Total Eruptions, Last Eruption Year, 
    and Mean/Median Time Between Eruptions by Volcano Type.
    """
    if df.empty:
        return dash_table.DataTable()

    # 1. Calculate Intervals
    # Sort by Type and Year to ensure correct diff calculation
    df_sorted = df.sort_values(['Type', 'Year'])
    
    # Calculate difference in years between consecutive eruptions within each Type
    df_sorted['Interval'] = df_sorted.groupby('Type')['Year'].diff()

    # 2. Aggregation
    stats = df_sorted.groupby('Type').agg(
        Total_Eruptions=('Name', 'count'),
        Last_Eruption=('Year', 'max'),
        Mean_Interval=('Interval', 'mean'),
        Median_Interval=('Interval', 'median')
    ).reset_index()

    # 3. Formatting
    # Sort by Total Eruptions descending
    stats = stats.sort_values('Total_Eruptions', ascending=False)

    # Format Last Eruption to be integer
    stats['Last_Eruption'] = stats['Last_Eruption'].fillna(0).astype(int)
    
    # Format Intervals (round to 1 decimal place, fill NaNs with 0 or -)
    stats['Mean_Interval'] = stats['Mean_Interval'].round(1).fillna('-')
    stats['Median_Interval'] = stats['Median_Interval'].round(1).fillna('-')

    # 4. Create DataTable
    table = dash_table.DataTable(
        data=stats.to_dict('records'),
        columns=[
            {'name': 'Volcano Type', 'id': 'Type'},
            {'name': 'Total Eruptions', 'id': 'Total_Eruptions'},
            {'name': 'Last Eruption Year', 'id': 'Last_Eruption'},
            {'name': 'Mean Interval (Years)', 'id': 'Mean_Interval'},
            {'name': 'Median Interval (Years)', 'id': 'Median_Interval'}
        ],
        style_header={
            'backgroundColor': '#333',
            'color': 'white',
            'fontWeight': 'bold',
            'border': '1px solid #444'
        },
        style_cell={
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'border': '1px solid #444',
            'textAlign': 'left',
            'padding': '10px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#252525'
            }
        ],
        page_size=10,
        style_table={'overflowX': 'auto'}
    )
    
    return table

# Initialize App
app = Dash(__name__)

# Load Data
df = load_data()
if df.empty:
    raise ValueError("CRITICAL ERROR: Data could not be loaded. Check 'volcano-events.tsv' path.")

# Styles
# Styles
CONTENT_STYLE = {
    "padding": "20px",
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
app.layout = html.Div(
    children=[
        html.H1("Volcano Insights Dashboard", style={'textAlign': 'center', 'color': 'white'}),
        html.P("Analyzing Significant Volcanic Eruptions", style={'textAlign': 'center', 'color': '#ccc'}),

        # ---------- Global Filters ----------
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Label("Year range", style={'color': 'white'}),
                        dcc.RangeSlider(
                            id="year-slider",
                            min=df['Year'].min(), # Assuming df is available here
                            max=2025, # Assuming a max year
                            value=[df['Year'].min(), 2025],
                            step=10,
                            marks={str(y): {'label': str(y), 'style': {'color': 'white'}} for y in range(int(df['Year'].min()), 2025 + 1, 500)},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ],
                    style={"flex": "2", "marginRight": "30px"},
                ),
                html.Div(
                    children=[
                        html.Label("Country", style={'color': 'white'}),
                        dcc.Dropdown(
                            id="country-dropdown",
                            options=[{'label': c, 'value': c} for c in sorted(df['Country'].unique())], # Assuming df is available here
                            placeholder="All countries",
                            value=None,
                            clearable=True,
                            style={'color': 'black'}
                        ),
                    ],
                    style={"flex": "1"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "marginBottom": "30px", "padding": "20px", "backgroundColor": "#1e1e1e", "borderRadius": "10px"},
        ),

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
                html.H4("Total Damage", style={'color': '#888', 'font-size': '14px'}),
                html.H2(id='kpi-damage', style={'font-size': '32px'})
            ], style={**CARD_STYLE, 'flex': '1'})
        ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '20px'}),

        # ---------- Hero Section: Map ----------
        html.Div([
            dcc.Graph(id='map-graph', style={'height': '600px', 'width': '100%'}),
            # Map Controls
            html.Div([
                dcc.Store(id='map-mode-store', data='distribution'),
                # Selection Buttons
                html.Div([
                    dcc.Store(id='map-selection-store', data='all'),
                    html.Button('Select All', id='btn-select-all', style={
                        'backgroundColor': '#333', 'color': '#ff5722', 
                        'border': '1px solid #ff5722', 'padding': '5px 15px', 'marginRight': '5px', 'borderRadius': '5px', 'cursor': 'pointer'
                    }),
                    html.Button('Unselect All', id='btn-unselect-all', style={
                        'backgroundColor': '#333', 'color': '#ff5722', 
                        'border': '1px solid #ff5722', 'padding': '5px 15px', 'borderRadius': '5px', 'cursor': 'pointer'
                    })
                ], style={'display': 'flex', 'width': '100%', 'marginBottom': '10px', 'justifyContent': 'flex-end'}),

                html.Div([
                    html.Div("Global Volcano Distribution", id='btn-distribution', n_clicks=0, style={
                        'flex-grow': '3', 'background-color': '#ff5722', 'color': 'white', 
                        'padding': '10px', 'margin-right': '5px', 'border-radius': '5px', 
                        'cursor': 'pointer', 'text-align': 'center', 'overflow': 'hidden', 'white-space': 'nowrap', 'transition': 'all 0.5s ease'
                    }),
                    html.Div("Frequency", id='btn-frequency', n_clicks=0, style={
                        'flex-grow': '1', 'background-color': '#333', 'color': '#888', 
                        'padding': '10px', 'margin-right': '5px', 'border-radius': '5px', 
                        'cursor': 'pointer', 'text-align': 'center', 'overflow': 'hidden', 'white-space': 'nowrap', 'transition': 'all 0.5s ease'
                    }),
                    html.Div("Total Deaths", id='btn-deaths', n_clicks=0, style={
                        'flex-grow': '1', 'background-color': '#333', 'color': '#888', 
                        'padding': '10px', 'margin-right': '5px', 'border-radius': '5px', 
                        'cursor': 'pointer', 'text-align': 'center', 'overflow': 'hidden', 'white-space': 'nowrap', 'transition': 'all 0.5s ease'
                    }),
                    html.Div("Total Damage", id='btn-damage', n_clicks=0, style={
                        'flex-grow': '1', 'background-color': '#333', 'color': '#888', 
                        'padding': '10px', 'border-radius': '5px', 
                        'cursor': 'pointer', 'text-align': 'center', 'overflow': 'hidden', 'white-space': 'nowrap', 'transition': 'all 0.5s ease'
                    })
                ], style={'display': 'flex', 'width': '100%', 'justify-content': 'center'})
            ], style={'marginTop': '10px'}),
            
            # Dynamic Insight Text
            html.Div(id='map-insight', style={
                'marginTop': '15px', 'padding': '15px', 'borderLeft': '4px solid #ff5722',
                'backgroundColor': '#252525', 'color': '#ddd', 'fontStyle': 'italic'
            })
        ], style={**CARD_STYLE, 'padding': '10px'}), 
        
        # Time Series Row
        html.Div([
             html.Div([
                create_expanding_buttons(
                    'time',
                    [
                        {'label': 'Year', 'value': 'year'},
                        {'label': 'Century', 'value': 'century'},
                        {'label': 'Smooth (10y Avg)', 'value': 'smooth'},
                        {'label': 'Forecast (Prophet)', 'value': 'forecast'}
                    ],
                    'year'
                ),
                dcc.Graph(id='time-graph', style={'height': '320px'}),
                html.Div(id='forecast-disclaimer', style={'textAlign': 'center', 'color': '#ff9800', 'fontStyle': 'italic', 'marginTop': '10px'}),
                
                # Dynamic Temporal Insight Text
                html.Div(id='temporal-insight', style={
                    'marginTop': '15px', 'padding': '15px', 'borderLeft': '4px solid #ff5722',
                    'backgroundColor': '#252525', 'color': '#ddd', 'fontStyle': 'italic'
                })
            ], style={**CARD_STYLE, 'flex': '1'})
        ], style={'display': 'flex', 'margin-bottom': '20px'}),

        # =============================================================================
        # NARRATIVE SECTION 1: The Pareto Principle of Death
        # =============================================================================
        html.Div([
            html.H2("1. The Pareto Principle of Death", style={'color': '#ff5722', 'borderBottom': '2px solid #ff5722', 'paddingBottom': '10px'}),
            html.P([
                html.B("Insight: "), "Volcanic fatalities follow a 'Power Law'. The vast majority of eruptions are harmless. ",
                "A tiny fraction (<1%) of events (like Tambora, Krakatau, Pelee) account for >80% of historical deaths. ",
                "The Top 10 countries alone account for the vast majority of all recorded fatalities.",
                html.Br(),
                html.B("Conclusion: "), "Disaster planning shouldn't focus on average eruptions, but on extreme outliers."
            ], style={'fontSize': '16px', 'marginBottom': '20px'}),
            
            html.Div([
                html.Div([dcc.Graph(id='pareto-chart', style={'height': '400px'})], style={**CARD_STYLE, 'flex': '1', 'marginRight': '20px'}),
                html.Div([dcc.Graph(id='loglog-plot', style={'height': '400px'})], style={**CARD_STYLE, 'flex': '1'})
            ], style={'display': 'flex'})
        ], style={'marginBottom': '60px'}),


        # =============================================================================
        # NARRATIVE SECTION 2: The Matrix of Threat
        # =============================================================================
        html.Div([
            html.H2("2. The Matrix of Threat", style={'color': '#ff5722', 'borderBottom': '2px solid #ff5722', 'paddingBottom': '10px'}),
            html.P([
                html.B("Insight: "), "Stratovolcanoes are responsible for the most total deaths (217k+), simply due to their frequency. ",
                "However, Calderas are the deadliest *per event* (avg ~1,100 deaths), followed by Maars.",
                html.Br(),
                html.B("Conclusion: "), "Risk = Probability x Impact. Stratovolcanoes are high probability/high impact, while Calderas are low probability/extreme impact."
            ], style={'fontSize': '16px', 'marginBottom': '20px'}),

            html.Div([
                html.Div([dcc.Graph(id='deaths-injuries-graph', style={'height': '500px'})], style={**CARD_STYLE, 'flex': '1'}) # This is the Risk Matrix (get_type_vs_frequency)
            ], style={'display': 'flex'})
        ], style={'marginBottom': '60px'}),

        # =============================================================================
        # NARRATIVE SECTION 3: The Indirect Killer
        # =============================================================================
        html.Div([
            html.H2("3. The Indirect Killer", style={'color': '#ff5722', 'borderBottom': '2px solid #ff5722', 'paddingBottom': '10px'}),
            html.P([
                html.B("Insight: "), "Pyroclastic Flows are the #1 historical killer (182k+ deaths), followed by Tsunamis (137k+). ",
                "Surprisingly, 'Indirect' causes (starvation, disease) are the 3rd deadliest category (112k+), often more lethal than direct lava flows.",
                html.Br(),
                html.B("Conclusion: "), "While 'Tephra' (ash) is the most frequent hazard, flows and waves are the true mass killers."
            ], style={'fontSize': '16px', 'marginBottom': '20px'}),

            html.Div([
                # Secondary Hazards Bar Chart
                html.Div([
                    html.Div([
                        create_expanding_buttons(
                            'secondary',
                            [
                                {'label': 'Median Deaths', 'value': 'median'},
                                {'label': 'Mean Deaths', 'value': 'mean'},
                                {'label': 'Total Deaths (All)', 'value': 'sum'},
                                {'label': 'Median (Agents)', 'value': 'median_agents'},
                                {'label': 'Mean (Agents)', 'value': 'mean_agents'},
                                {'label': 'Total (Agents)', 'value': 'sum_agents'}
                            ],
                            'mean'
                        ),
                    ], style={'textAlign': 'center'}),
                    dcc.Graph(id='with_and_without_indirect_deaths_by_type', style={'height': '400px'})
                ], style={**CARD_STYLE, 'flex': '1', 'marginRight': '20px'}),

                # Heatmap
                html.Div([
                    html.Div([
                        create_expanding_buttons(
                            'heatmap',
                            [
                                {'label': 'Count', 'value': 'count'},
                                {'label': 'Risk Percentage', 'value': 'percent'}
                            ],
                            'count'
                        )
                    ]),
                    dcc.Graph(id='vei-deaths-graph', style={'height': '400px', 'width': '100%'}) 
                ], style={**CARD_STYLE, 'flex': '1'})
            ], style={'display': 'flex'})
        ], style={'marginBottom': '60px'}),

        # =============================================================================
        # DETAILED EXPLORATION (Tabs)
        # =============================================================================
        html.H2("Detailed Exploration", style={'color': 'white', 'borderBottom': '1px solid #333', 'paddingBottom': '10px'}),
        dcc.Tabs(
            id="tabs",
            value="tab-global",
            colors={"border": "#1e1e1e", "primary": "#ff5722", "background": "#333"},
            children=[
                # Tab 1 : Global Impact
                dcc.Tab(
                    label="Global Impact",
                    value="tab-global",
                    children=[
                        html.Div(
                            children=[
                                html.Div([dcc.Graph(id="impact-graph", style={'height': '400px'})], style={**CARD_STYLE}), # Top 10 Eruptions
                                html.Div([dcc.Graph(id="top_countries_by_historical_deaths", style={'height': '400px'})], style={**CARD_STYLE}),
                                
                                # VEI Analysis
                                html.Div([
                                    html.Div([
                                        create_expanding_buttons(
                                            'vei',
                                            [
                                                {'label': 'Median Deaths', 'value': 'median'},
                                                {'label': 'Mean Deaths', 'value': 'mean'},
                                                {'label': 'Total Deaths', 'value': 'sum'},
                                                {'label': 'Total Eruptions', 'value': 'count'}
                                            ],
                                            'median'
                                        ),
                                    ], style={'textAlign': 'center'}),
                                    dcc.Graph(id='median_deaths_by_VIE', style={'height': '400px'})
                                ], style={**CARD_STYLE}),

                                # Volcano Type Analysis
                                html.Div([
                                    html.Div([
                                        create_expanding_buttons(
                                            'type_metric',
                                            [
                                                {'label': 'Total Deaths', 'value': 'total'},
                                                {'label': 'Deaths/Eruption', 'value': 'rate'}
                                            ],
                                            'total'
                                        ),
                                    ], style={'textAlign': 'center'}),
                                    html.Div([
                                        create_expanding_buttons(
                                            'type_scale',
                                            [
                                                {'label': 'Log Scale', 'value': 'log'},
                                                {'label': 'Linear Scale', 'value': 'linear'}
                                            ],
                                            'log'
                                        ),
                                    ], style={'textAlign': 'center', 'marginTop': '5px'}),
                                    dcc.Graph(id='volcano_type', style={'height': '400px'}),
                                ], style={**CARD_STYLE}),
                                
                                # Volcano Type Statistics Table
                                html.Div([
                                    html.H4("Volcano Type Statistics", style={'color': '#888', 'marginBottom': '10px'}),
                                    html.Div(id='volcano-stats-table-container')
                                ], style={**CARD_STYLE, 'gridColumn': '1 / -1'}), # Span full width
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                    style={'backgroundColor': '#1e1e1e', 'color': 'white'},
                    selected_style={'backgroundColor': '#ff5722', 'color': 'white'}
                ),

                # Tab 2 : Regional Analysis
                dcc.Tab(
                    label="Regional Analysis",
                    value="tab-regions",
                    children=[
                        html.Div(
                            children=[
                                html.Div([dcc.Graph(id="top10-deadliest-regions", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="region-volcano-sunburst", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="volcano-treemap", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="volcano-donut", style={'height': '400px'})], style={**CARD_STYLE}),
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                    style={'backgroundColor': '#1e1e1e', 'color': 'white'},
                    selected_style={'backgroundColor': '#ff5722', 'color': 'white'}
                ),

                # Tab 3 : Injury Analysis
                dcc.Tab(
                    label="Injury Analysis",
                    value="tab-injuries",
                    children=[
                        html.Div(
                            children=[
                                html.Div([dcc.Graph(id="deaths-vs-injuries-scatter", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="deaths-vs-injuries-bubble", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="injury-ratio-bar", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="injury-ratio-scatter", style={'height': '400px'})], style={**CARD_STYLE}),
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                    style={'backgroundColor': '#1e1e1e', 'color': 'white'},
                    selected_style={'backgroundColor': '#ff5722', 'color': 'white'}
                ),

                # Tab 4 : Distributions & Risk
                dcc.Tab(
                    label="Distributions & Risk",
                    value="tab-distributions",
                    children=[
                        html.Div(
                            children=[
                                html.Div([dcc.Graph(id="death-boxplot", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="death-boxplot-by-type", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="correlation-heatmap", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="deaths-damage-graph", style={'height': '400px'})], style={**CARD_STYLE}),
                                html.Div([dcc.Graph(id="elevation-vei-graph", style={'height': '400px'})], style={**CARD_STYLE}),
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                    style={'backgroundColor': '#1e1e1e', 'color': 'white'},
                    selected_style={'backgroundColor': '#ff5722', 'color': 'white'}
                ),
            ],
        ),

    ], style=CONTENT_STYLE)

@app.callback(
    [Output('map-mode-store', 'data'),
     Output('btn-distribution', 'style'),
     Output('btn-frequency', 'style'),
     Output('btn-deaths', 'style'),
     Output('btn-damage', 'style'),
     Output('btn-distribution', 'children'),
     Output('btn-frequency', 'children'),
     Output('btn-deaths', 'children'),
     Output('btn-damage', 'children')],
    [Input('btn-distribution', 'n_clicks'),
     Input('btn-frequency', 'n_clicks'),
     Input('btn-deaths', 'n_clicks'),
     Input('btn-damage', 'n_clicks')],
    [State('btn-distribution', 'style'),
     State('btn-frequency', 'style'),
     State('btn-deaths', 'style'),
     State('btn-damage', 'style')]
)
def update_map_mode(n1, n2, n3, n4, s1, s2, s3, s4):
    ctx_msg = ctx.triggered_id
    if not ctx_msg:
        return 'distribution', s1, s2, s3, s4, "Global Volcano Distribution", "Frequency", "Total Deaths", "Total Damage"

    mode_map = {
        'btn-distribution': 'distribution',
        'btn-frequency': 'frequency',
        'btn-deaths': 'deaths',
        'btn-damage': 'damage'
    }
    
    new_mode = mode_map.get(ctx_msg, 'distribution')
    
    # Base style for all buttons
    base_style = {
        'padding': '10px', 'margin-right': '5px', 'border-radius': '5px', 
        'cursor': 'pointer', 'text-align': 'center', 'overflow': 'hidden', 
        'white-space': 'nowrap', 'transition': 'all 0.5s ease'
    }
    
    # Define styles and text for each state
    styles = []
    texts = []
    
    buttons = ['btn-distribution', 'btn-frequency', 'btn-deaths', 'btn-damage']
    full_texts = ["Global Volcano Distribution", "Eruption Frequency by Country", "Total Deaths by Country", "Total Damage by Country"]
    short_texts = ["Distribution", "Frequency", "Deaths", "Damage"]
    
    for i, btn in enumerate(buttons):
        style = base_style.copy()
        if btn == ctx_msg:
            style['flex-grow'] = '3'
            style['background-color'] = '#ff5722'
            style['color'] = 'white'
            texts.append(full_texts[i])
        else:
            style['flex-grow'] = '1'
            style['background-color'] = '#333'
            style['color'] = '#888'
            texts.append(short_texts[i])
        styles.append(style)
        
    return new_mode, styles[0], styles[1], styles[2], styles[3], texts[0], texts[1], texts[2], texts[3]

def create_button_callback(group_id, options):
    """
    Creates a callback for a group of expanding buttons.
    """
    inputs = [Input(f'btn-{group_id}-{opt["value"]}', 'n_clicks') for opt in options]
    states = [State(f'btn-{group_id}-{opt["value"]}', 'style') for opt in options]
    
    outputs = [Output(f'{group_id}-store', 'data')] + \
              [Output(f'btn-{group_id}-{opt["value"]}', 'style') for opt in options]
    
    @app.callback(outputs, inputs, states)
    def update_buttons(*args):
        n_clicks = args[:len(options)]
        styles = args[len(options):]
        
        ctx_msg = ctx.triggered_id
        default_value = options[0]['value']
        
        if not ctx_msg:
            # On initial load, just return the current state (or default)
            # But wait, we need to return the store data and styles.
            # If we don't know the current store data, we default to the first option.
            # Actually, the layout sets the initial style.
            # We can just return the default value and current styles.
            return default_value, *styles

        # Determine which button was clicked
        clicked_value = default_value
        for opt in options:
            if f'btn-{group_id}-{opt["value"]}' == ctx_msg:
                clicked_value = opt['value']
                break
        
        new_styles = []
        for i, opt in enumerate(options):
            style = styles[i].copy()
            if opt['value'] == clicked_value:
                style['flex-grow'] = '3'
                style['background-color'] = '#ff5722'
                style['color'] = 'white'
            else:
                style['flex-grow'] = '1'
                style['background-color'] = '#333'
                style['color'] = '#888'
            new_styles.append(style)
            
        return clicked_value, *new_styles

# Create callbacks for each group
create_button_callback('time', [
    {'label': 'Year', 'value': 'year'},
    {'label': 'Century', 'value': 'century'},
    {'label': 'Smooth (10y Avg)', 'value': 'smooth'},
    {'label': 'Forecast (Prophet)', 'value': 'forecast'}
])

create_button_callback('vei', [
    {'label': 'Median Deaths', 'value': 'median'},
    {'label': 'Mean Deaths', 'value': 'mean'},
    {'label': 'Total Deaths', 'value': 'sum'},
    {'label': 'Total Eruptions', 'value': 'count'}
])

create_button_callback('secondary', [
    {'label': 'Median Deaths', 'value': 'median'},
    {'label': 'Mean Deaths', 'value': 'mean'},
    {'label': 'Total Deaths (All)', 'value': 'sum'},
    {'label': 'Median (Agents)', 'value': 'median_agents'},
    {'label': 'Mean (Agents)', 'value': 'mean_agents'},
    {'label': 'Total (Agents)', 'value': 'sum_agents'}
])

create_button_callback('type_scale', [
    {'label': 'Log Scale', 'value': 'log'},
    {'label': 'Linear Scale', 'value': 'linear'}
])

create_button_callback('type_metric', [
    {'label': 'Total Deaths', 'value': 'total'},
    {'label': 'Deaths/Eruption', 'value': 'rate'}
])



create_button_callback('heatmap', [
    {'label': 'Count', 'value': 'count'},
    {'label': 'Risk Percentage', 'value': 'percent'}
])

@app.callback(
    Output('map-selection-store', 'data'),
    [Input('btn-select-all', 'n_clicks'),
     Input('btn-unselect-all', 'n_clicks')],
    prevent_initial_call=True
)
def update_selection_store(n_select, n_unselect):
    ctx_msg = ctx.triggered_id
    if ctx_msg == 'btn-select-all':
        return 'all'
    elif ctx_msg == 'btn-unselect-all':
        return 'none'
    return 'all'

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
     Output('kpi-damage', 'children'),
     Output('forecast-disclaimer', 'children'),
     Output('temporal-insight', 'children'),
     # New Outputs
     Output('top10-deadliest-regions', 'figure'),
     Output('region-volcano-sunburst', 'figure'),
     Output('volcano-treemap', 'figure'),
     Output('volcano-donut', 'figure'),
     Output('deaths-vs-injuries-scatter', 'figure'),
     Output('deaths-vs-injuries-bubble', 'figure'),
     Output('injury-ratio-bar', 'figure'),
     Output('injury-ratio-scatter', 'figure'),
     Output('death-boxplot', 'figure'),
     Output('death-boxplot-by-type', 'figure'),
     Output('pareto-chart', 'figure'),
     Output('loglog-plot', 'figure'),
     Output('correlation-heatmap', 'figure'),
     Output('volcano-stats-table-container', 'children')],
    [Input('country-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('vei-store', 'data'),
     Input('secondary-store', 'data'),
     Input('heatmap-store', 'data'),
     Input('map-mode-store', 'data'),
     Input('time-store', 'data'),
     Input('type_scale-store', 'data'),
     Input('type_metric-store', 'data'),
     Input('map-selection-store', 'data')] 
)
def update_dashboard(selected_country, year_range, selected_vei_metric, selected_secondary_metric, selected_heatmap_metric, map_mode, time_mode, type_scale, type_metric, map_selection):
    # 1. Check if callback fires
    print("CALLBACK FIRED") 
    
    # 2. Check Data
    dff = df.copy()
    if selected_country:
        dff = dff[dff['Country'] == selected_country]
    
    # 3. Check if data survived filtering
    print(f"Rows remaining after filter: {len(dff)}")
    # Filter Data
    print(f"DEBUG: Starting update_dashboard. Country={selected_country}, Year={year_range}", flush=True)
    dff = df.copy()
    print(f"DEBUG: Initial dff shape: {dff.shape}", flush=True)

    if selected_country:
        dff = dff[dff['Country'] == selected_country]
        print(f"DEBUG: dff shape after country filter: {dff.shape}")
    
    if year_range:
        dff = dff[(dff['Year'] >= year_range[0]) & (dff['Year'] <= year_range[1])]
        print(f"DEBUG: dff shape after year filter: {dff.shape}")

    if dff.empty:
        dff = df # Fallback if empty

    # KPIs
    total_eruptions = len(dff)
    total_deaths = f"{int(dff['Deaths'].sum()):,}"
    total_damage = f"${dff['Damage_Millions'].sum()*1000000:,.0f}"

    # Figures
    if map_mode == 'distribution':
        fig1 = get_map_points(dff)
        
        # Apply selection
        if map_selection == 'none':
            fig1.for_each_trace(lambda trace: trace.update(visible='legendonly'))
        elif map_selection == 'all':
            fig1.for_each_trace(lambda trace: trace.update(visible=True))
            
    elif map_mode == 'frequency':
        # Create a count column for aggregation
        dff_map = dff.copy()
        dff_map['Frequency'] = 1
        fig1 = get_country_choropleth(dff_map, 'Frequency', "Eruption Frequency by Country", "Eruptions")
    elif map_mode == 'deaths':
        fig1 = get_country_choropleth(dff, 'Total_Deaths', "Total Deaths by Country", "Deaths")
    elif map_mode == 'damage':
        fig1 = get_country_choropleth(dff, 'Total_Damage_Millions', "Total Damage by Country", "Damage ($M)")
    else:
        fig1 = get_map_points(dff) # Fallback

    fig2 = render_temporal_series(dff, mode=time_mode)
    fig3 = get_impact_figure(dff)
    
    # MODIFIED: Pass the new selector value to the VEI function
    fig_vei = get_vei_analysis_figure(dff, selected_vei_metric)
    
    fig_top_countries = get_top_countries_by_historical_deaths_figure(dff)
    fig_indirect = get_with_and_without_indirect_deaths_by_type_figure(dff, selected_secondary_metric)
    fig_volcano_type = get_volcano_type_figure(dff, type_scale, type_metric)
    
    # New Graphs
    fig_vei_deaths = volcano_type_vs_hasard_heatmap(dff, normalize=(selected_heatmap_metric == 'percent'))
    fig_deaths_injuries = get_type_vs_frequency(dff)
    fig_deaths_damage = get_deaths_vs_damage_figure(dff)
    fig_elevation_vei = get_elevation_vs_vei_figure(dff)
    
    # --- NEW GRAPHS GENERATION ---
    # Regional
    fig_regions = impact.render_top10_deadliest_regions(dff)
    fig_sunburst = impact.render_region_volcano_sunburst(dff)
    fig_treemap = impact.render_deadliest_volcanoes_treemap(dff)
    fig_donut = impact.render_deadliest_volcanoes_donut(dff)
    
    # Injuries
    fig_inj_scatter = impact.render_deaths_vs_injuries_scatter(dff)
    fig_inj_bubble = impact.render_deaths_vs_injuries_bubble(dff)
    fig_inj_ratio = impact.render_top10_injury_ratio(dff)
    fig_inj_ratio_sc = impact.render_injury_ratio_scatter(dff)
    
    # Distributions
    fig_boxplot = impact.render_death_boxplot(dff)
    fig_boxplot_type = impact.render_death_boxplot_by_type(dff)
    fig_pareto = impact.render_pareto_chart(dff)
    fig_loglog = impact.render_loglog_heavytail(dff)
    fig_corr = impact.render_correlation_heatmap(dff)
    
    # Table
    table_stats = get_volcano_type_stats_table(dff)

    return (
        fig1, fig2, fig3, fig_vei, fig_top_countries, fig_indirect, fig_volcano_type, 
        fig_vei_deaths, fig_deaths_injuries, fig_deaths_damage, fig_elevation_vei,
        total_eruptions, total_deaths, total_damage, 
        "The number of eruptions over time tends to increase due to more data being collected over the years. Forecasting eruptions on past data is therefore irrelevant. The unpredictibility of eruptions makes them dangerous, we will look at how we can mitigate their impact.",
        f"Temporal analysis shows {len(dff)} eruptions in this period.",
        fig_regions, fig_sunburst, fig_treemap, fig_donut,
        fig_inj_scatter, fig_inj_bubble, fig_inj_ratio, fig_inj_ratio_sc,
        fig_boxplot, fig_boxplot_type, fig_pareto, fig_loglog, fig_corr,
        table_stats
    )

    # Disclaimer Logic
    disclaimer_text = ""
    # if time_mode == 'forecast':
    #     disclaimer_text = "..." # Moved to temporal_insight

    # Temporal Insight Logic
    temporal_insight = ""
    if time_mode in ['year', 'century', 'smooth']:
        temporal_insight = "The observed increase in eruptions over time is primarily due to improved data collection and reporting, not necessarily a geological increase. Volcanic eruptions remain largely unpredictable events."
    elif time_mode == 'forecast':
        temporal_insight = "The forecast is false as it predicts growing eruptions in the future but this is due to a 'trend' of growing volcano activity in the data due to more data being collected over the years"

    return (fig1, fig2, fig3, fig_vei, fig_top_countries, fig_indirect, fig_volcano_type, 
            fig_vei_deaths, fig_deaths_injuries, fig_deaths_damage, fig_elevation_vei, 
            total_eruptions, total_deaths, total_damage, disclaimer_text, temporal_insight,
            # New Returns
            fig_regions, fig_sunburst, fig_treemap, fig_donut,
            fig_inj_scatter, fig_inj_bubble, fig_inj_ratio, fig_inj_ratio_sc,
            fig_boxplot, fig_boxplot_type, fig_pareto, fig_loglog, fig_corr)

@app.callback(
    Output('map-insight', 'children'),
    Input('map-mode-store', 'data')
)
def update_map_insight(mode):
    if mode == 'distribution':
        return "Looking at volcanoe distribution around the world, alows us to see the 'Ring of Fire' phenomenom in the Pacific where most volcanoes are concentrated."
    elif mode == 'frequency':
        return "The frequency of volcanoes is also seen primarily in the Ring of Fire and especially Indonesia, with some outliers like Italy and Iceland."
    elif mode == 'deaths':
        return "The death map is practically the same as the frequency map, which is to be expected as more eruptions naturally implies more deaths. The difference observed between the two can be explained by two main factors, countries with high frequency but low deaths can be due to volcano eruptions happening in sparsely populated areas (like Russia), or countries with better infrastructure helping mitigate the fatalities per eruption."
    elif mode == 'damage':
        return "Finally, total damage reflects economic data as the countries with the most damage are first world countries where infrastructure is more costly (USA, Italy, Spain), even though some of these like Spain had very few deaths and eruptions. Indonesia still appears in this graph as the sheer number of eruptions compensates the lower standards of living."
    return ""

if __name__ == '__main__':
    print("Launching Dashboard...")
    print("Dashboard launched at: http://127.0.0.1:8051")
    app.run( # Runs the dashboard
        host='127.0.0.1', # Localhost adress on which the dashboard is running
        port=8051, # Port number on which the dashboard is running
        debug=True, # Get's rid of debug console (white widget at bottom right of screen)
        )
