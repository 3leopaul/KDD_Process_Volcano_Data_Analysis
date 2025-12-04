import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- Helper for Dark Theme Layout ---
def update_layout(fig, title="", x_title="", y_title=""):
    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig

# --- Tab 1: Overview ---

def render_top10_deadliest_eruptions(df):
    # Top 10 eruptions by Total Deaths
    if df.empty: return go.Figure()
    dff = df.sort_values("Total_Deaths", ascending=False).head(10)
    fig = px.bar(dff, x="Total_Deaths", y="Name", orientation='h',
                 text="Total_Deaths", color="Total_Deaths", color_continuous_scale="Reds")
    fig.update_traces(textposition='outside')
    fig.update_yaxes(autorange="reversed") # Top 1 at top
    return update_layout(fig, "Top 10 Deadliest Eruptions", "Total Deaths", "Volcano Name")

def render_top10_deadliest_volcanoes(df):
    # Group by Volcano Name (some have multiple eruptions)
    if df.empty: return go.Figure()
    dff = df.groupby("Name")["Total_Deaths"].sum().reset_index()
    dff = dff.sort_values("Total_Deaths", ascending=False).head(10)
    fig = px.bar(dff, x="Total_Deaths", y="Name", orientation='h',
                 text="Total_Deaths", color="Total_Deaths", color_continuous_scale="Reds")
    fig.update_traces(textposition='outside')
    fig.update_yaxes(autorange="reversed")
    return update_layout(fig, "Top 10 Deadliest Volcanoes (All Time)", "Total Deaths", "Volcano Name")

def render_top10_deadliest_countries(df):
    if df.empty: return go.Figure()
    dff = df.groupby("Country")["Total_Deaths"].sum().reset_index()
    dff = dff.sort_values("Total_Deaths", ascending=False).head(10)
    fig = px.bar(dff, x="Total_Deaths", y="Country", orientation='h',
                 text="Total_Deaths", color="Total_Deaths", color_continuous_scale="Reds")
    fig.update_traces(textposition='outside')
    fig.update_yaxes(autorange="reversed")
    return update_layout(fig, "Top 10 Deadliest Countries", "Total Deaths", "Country")

def render_deaths_over_time(df):
    # Scatter/Line of deaths over years
    if df.empty: return go.Figure()
    dff = df.groupby("Year")["Total_Deaths"].sum().reset_index()
    fig = px.bar(dff, x="Year", y="Total_Deaths", color="Total_Deaths", color_continuous_scale="Reds")
    return update_layout(fig, "Fatalities Over Time", "Year", "Total Deaths")

# --- Tab 2: Regions & Volcanoes ---

def render_top10_deadliest_regions(df):
    # Assuming 'Location' is Region
    if df.empty: return go.Figure()
    dff = df.groupby("Location")["Total_Deaths"].sum().reset_index()
    dff = dff.sort_values("Total_Deaths", ascending=False).head(10)
    fig = px.bar(dff, x="Total_Deaths", y="Location", orientation='h',
                 text="Total_Deaths", color="Total_Deaths", color_continuous_scale="Reds")
    fig.update_traces(textposition='outside')
    fig.update_yaxes(autorange="reversed")
    return update_layout(fig, "Top 10 Deadliest Regions", "Total Deaths", "Region")

def render_region_volcano_sunburst(df):
    # Hierarchy: Country -> Location -> Name
    if df.empty: return go.Figure()
    dff = df[df["Total_Deaths"] > 0].copy()
    if dff.empty: return go.Figure()
    fig = px.sunburst(dff, path=['Country', 'Location', 'Name'], values='Total_Deaths',
                      color='Total_Deaths', color_continuous_scale='Reds')
    return update_layout(fig, "Regional Hierarchy of Fatalities")

def render_deadliest_volcanoes_treemap(df):
    if df.empty: return go.Figure()
    dff = df[df["Total_Deaths"] > 0].copy()
    if dff.empty: return go.Figure()
    fig = px.treemap(dff, path=['Country', 'Type', 'Name'], values='Total_Deaths',
                     color='Total_Deaths', color_continuous_scale='Reds')
    return update_layout(fig, "Treemap of Fatalities by Country & Type")

def render_deadliest_volcanoes_donut(df):
    # Share of deaths by Volcano Type
    if df.empty: return go.Figure()
    dff = df.groupby("Type")["Total_Deaths"].sum().reset_index()
    
    # Group small percentages (< 1%) into 'Other'
    total_deaths = dff["Total_Deaths"].sum()
    if total_deaths > 0:
        mask = dff["Total_Deaths"] / total_deaths >= 0.01
        large = dff[mask].copy()
        small_sum = dff[~mask]["Total_Deaths"].sum()
        
        if small_sum > 0:
            other_df = pd.DataFrame([{'Type': 'Other', 'Total_Deaths': small_sum}])
            dff = pd.concat([large, other_df], ignore_index=True)
        else:
            dff = large
        
    fig = px.pie(dff, values='Total_Deaths', names='Type', hole=0.4,
                 color_discrete_sequence=px.colors.sequential.Reds_r)
    return update_layout(fig, "Share of Fatalities by Volcano Type")

# --- Tab 3: Injuries & Ratios ---

def render_deaths_vs_injuries_scatter(df):
    if df.empty: return go.Figure()
    fig = px.scatter(df, x="Total_Injuries", y="Total_Deaths", color="Type",
                     hover_data=["Name", "Year", "Country"], log_x=True, log_y=True)
    return update_layout(fig, "Deaths vs Injuries (Log Scale)", "Injuries", "Deaths")

def render_deaths_vs_injuries_bubble(df):
    # Size = VEI or Damage? Let's use VEI
    if df.empty: return go.Figure()
    dff = df.copy()
    dff['VEI'] = dff['VEI'].fillna(0)
    # Ensure VEI is positive for size
    dff['VEI_Size'] = dff['VEI'].apply(lambda x: max(0.1, x))
    fig = px.scatter(dff, x="Total_Injuries", y="Total_Deaths", size="VEI_Size", color="Type",
                     hover_data=["Name", "Year", "VEI"], log_x=True, log_y=True)
    return update_layout(fig, "Deaths vs Injuries (Size = VEI)", "Injuries", "Deaths")

def render_top10_injury_ratio(df):
    # Ratio = Injuries / Deaths (for events with > 0 deaths)
    if df.empty: return go.Figure()
    dff = df[(df["Total_Deaths"] > 10) & (df["Total_Injuries"] > 0)].copy()
    if dff.empty: return go.Figure()
    dff["Injury_Death_Ratio"] = dff["Total_Injuries"] / dff["Total_Deaths"]
    dff = dff.sort_values("Injury_Death_Ratio", ascending=False).head(10)
    fig = px.bar(dff, x="Injury_Death_Ratio", y="Name", orientation='h',
                 text="Injury_Death_Ratio", color="Injury_Death_Ratio", color_continuous_scale="Viridis")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_yaxes(autorange="reversed")
    return update_layout(fig, "Top 10 Events by Injury/Death Ratio (>10 Deaths)", "Ratio (Injuries/Deaths)", "Volcano")

def render_injury_ratio_scatter(df):
    if df.empty: return go.Figure()
    dff = df[(df["Total_Deaths"] > 0) & (df["Total_Injuries"] > 0)].copy()
    if dff.empty: return go.Figure()
    dff["Injury_Death_Ratio"] = dff["Total_Injuries"] / dff["Total_Deaths"]
    fig = px.scatter(dff, x="Year", y="Injury_Death_Ratio", color="Type",
                     hover_data=["Name", "Country"], log_y=True)
    return update_layout(fig, "Injury/Death Ratio Over Time", "Year", "Ratio (Log)")

# --- Tab 4: Distributions & Risk ---

def render_death_boxplot(df):
    if df.empty: return go.Figure()
    dff = df[df["Total_Deaths"] > 0]
    fig = px.box(dff, y="Total_Deaths", log_y=True, points="all")
    return update_layout(fig, "Distribution of Fatalities (Log Scale)", "", "Deaths")

def render_death_boxplot_by_type(df):
    if df.empty: return go.Figure()
    dff = df[df["Total_Deaths"] > 0]
    fig = px.box(dff, x="Type", y="Total_Deaths", log_y=True, color="Type")
    return update_layout(fig, "Fatality Distribution by Volcano Type", "Type", "Deaths")

def render_pareto_chart(df):
    # Cumulative % of deaths
    if df.empty: return go.Figure()
    dff = df.sort_values("Total_Deaths", ascending=False).reset_index(drop=True)
    dff["Cumulative_Deaths"] = dff["Total_Deaths"].cumsum()
    total_deaths = dff["Total_Deaths"].sum()
    if total_deaths == 0: return go.Figure()
    
    dff["Cumulative_Percentage"] = 100 * dff["Cumulative_Deaths"] / total_deaths
    dff["Rank"] = dff.index + 1
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dff["Rank"], y=dff["Total_Deaths"], name="Deaths per Event", marker_color="#ff5722", opacity=0.6))
    fig.add_trace(go.Scatter(x=dff["Rank"], y=dff["Cumulative_Percentage"], name="Cumulative %", yaxis="y2", line=dict(color="white", width=2)))
    
    fig.update_layout(
        title=dict(text="Pareto Chart of Fatalities", x=0.5),
        xaxis_title="Rank (Event)",
        yaxis_title="Deaths",
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105], showgrid=False),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(x=0.5, y=0.9, xanchor='center')
    )
    return fig

def render_loglog_heavytail(df):
    # Rank-Frequency plot (Zipf's law check)
    if df.empty: return go.Figure()
    dff = df[df["Total_Deaths"] > 0].sort_values("Total_Deaths", ascending=False).reset_index(drop=True)
    dff["Rank"] = dff.index + 1
    fig = px.scatter(dff, x="Rank", y="Total_Deaths", log_x=True, log_y=True,
                     title="Log-Log Rank-Size Plot (Heavy Tail Analysis)")
    return update_layout(fig, "Log-Log Rank-Size Plot", "Rank", "Deaths")

def render_correlation_heatmap(df):
    # Select numerical columns
    if df.empty: return go.Figure()
    cols = ["Year", "VEI", "Total_Deaths", "Total_Injuries", "Total_Damage_Millions", "Elevation"]
    # Check which cols exist
    valid_cols = [c for c in cols if c in df.columns]
    if not valid_cols: return go.Figure()
    
    dff = df[valid_cols].corr()
    fig = px.imshow(dff, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
    return update_layout(fig, "Correlation Heatmap")
