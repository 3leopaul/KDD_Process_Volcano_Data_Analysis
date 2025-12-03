# src/components/impact_analysis.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. OVERVIEW GRAPHS ---

def render_top10_deadliest_eruptions(df):
    # Top 10 des éruptions (Bar Chart)
    # Préparation
    temp = df[['Name', 'Total Deaths']].copy().fillna(0)
    temp = temp[temp['Total Deaths'] > 0]
    temp = temp.sort_values(by='Total Deaths', ascending=False).head(10)
    
    fig = px.bar(
        temp,
        x='Total Deaths', y='Name', orientation='h',
        title='Top 10 Deadliest Eruptions',
        text='Total Deaths',
        color='Total Deaths', color_continuous_scale='Reds'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def render_top10_deadliest_volcanoes(df):
    # Top 10 des volcans (cumulés)
    temp = df.groupby('Name')['Total Deaths'].sum().reset_index()
    temp = temp[temp['Total Deaths'] > 0].sort_values(by='Total Deaths', ascending=False).head(10)
    
    fig = px.bar(
        temp,
        x='Name', y='Total Deaths',
        title='Top 10 Deadliest Volcanoes (Cumulative)',
        color='Total Deaths', color_continuous_scale='Reds'
    )
    return fig

def render_top10_deadliest_countries(df):
    # Top 10 Pays
    temp = df.groupby("Country")["Total Deaths"].sum().reset_index()
    temp = temp.sort_values(by="Total Deaths", ascending=False).head(10)
    
    fig = px.bar(
        temp,
        x='Country', y='Total Deaths',
        title='Top 10 Countries by Fatalities',
        text='Total Deaths'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis_type='log') # Log scale car l'Indonésie écrase tout
    return fig

def render_deaths_over_time(df):
    # Time Series
    temp = df.groupby('Year')['Total Deaths'].sum().reset_index()
    temp = temp[temp['Total Deaths'] > 0]
    
    fig = px.line(
        temp,
        x='Year', y='Total Deaths',
        title='Fatalities over Time',
        markers=True
    )
    return fig

# --- 2. REGIONS & VOLCANOES ---

def render_top10_deadliest_regions(df):
    # Bar Chart par région (pour compléter le Sunburst)
    temp = df.groupby('Location')['Total Deaths'].sum().reset_index()
    temp = temp.sort_values(by='Total Deaths', ascending=False).head(10)
    
    fig = px.bar(
        temp, x='Total Deaths', y='Location', orientation='h',
        title='Top 10 Deadliest Regions'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def render_region_volcano_sunburst(df):
    # Sunburst (Pays -> Location)
    temp = df.groupby(['Country', 'Location'], as_index=False)['Total Deaths'].sum()
    temp = temp[temp['Total Deaths'] > 0].sort_values(by='Total Deaths', ascending=False).head(50)
    
    fig = px.sunburst(
        temp,
        path=['Country', 'Location'],
        values='Total Deaths',
        title='Fatalities Hierarchy (Country > Region)',
        color='Total Deaths', color_continuous_scale='RdBu_r'
    )
    return fig

def render_deadliest_volcanoes_treemap(df):
    # Treemap des volcans
    temp = df.groupby('Name')['Total Deaths'].sum().reset_index()
    temp = temp[temp['Total Deaths'] > 0].sort_values(by='Total Deaths', ascending=False).head(30)
    
    fig = px.treemap(
        temp,
        path=['Name'], values='Total Deaths',
        title='Top 30 Deadliest Volcanoes (Treemap)',
        color='Total Deaths', color_continuous_scale='Reds'
    )
    return fig

def render_deadliest_volcanoes_donut(df):
    # Donut Chart
    temp = df.groupby('Name')['Total Deaths'].sum().reset_index()
    temp = temp.sort_values(by='Total Deaths', ascending=False).head(10)
    
    fig = px.pie(
        temp,
        names='Name', values='Total Deaths',
        hole=0.4,
        title='Share of Deaths (Top 10 Volcanoes)'
    )
    return fig

# --- 3. INJURIES & RATIOS ---

def render_deaths_vs_injuries_scatter(df):
    # Scatter Log-Log
    temp = df[(df['Total Deaths']>0) | (df['Total Injuries']>0)].copy()
    temp = temp.fillna(0)
    
    fig = px.scatter(
        temp,
        x='Total Deaths', y='Total Injuries',
        hover_data=['Name', 'Year', 'Country'],
        title='Deaths vs Injuries (Log Scale)',
        log_x=True, log_y=True
    )
    return fig

def render_deaths_vs_injuries_bubble(df):
    # Bubble Chart
    temp = df[(df['Total Deaths']>0) | (df['Total Injuries']>0)].copy()
    temp = temp.fillna(0)
    
    fig = px.scatter(
        temp,
        x='Total Deaths', y='Total Injuries',
        size='Total Deaths', # La taille dépend des morts
        color='Total Injuries',
        title='Bubble: Deaths vs Injuries',
        hover_data=['Name', 'Year']
    )
    return fig

def render_top10_injury_ratio(df):
    # Bar chart Ratio
    temp = df.copy()
    # Calcul safe du ratio
    temp = temp[temp['Total Deaths'] > 0] # Eviter division par 0
    temp['Injury_Death_Ratio'] = temp['Total Injuries'].fillna(0) / temp['Total Deaths']
    
    top10 = temp.sort_values(by='Injury_Death_Ratio', ascending=False).head(10)
    
    fig = px.bar(
        top10,
        x='Injury_Death_Ratio', y='Name', orientation='h',
        title='Top 10 Events by Injury/Death Ratio'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def render_injury_ratio_scatter(df):
    # Scatter Ratio vs Deaths
    temp = df.copy()
    temp = temp[temp['Total Deaths'] > 0]
    temp['Injury_Death_Ratio'] = temp['Total Injuries'].fillna(0) / temp['Total Deaths']
    
    fig = px.scatter(
        temp,
        x='Total Deaths', y='Injury_Death_Ratio',
        log_x=True,
        title='Ratio vs Fatalities Magnitude'
    )
    return fig

# --- 4. DISTRIBUTIONS & RISK ---

def render_death_boxplot(df):
    # Boxplot global
    temp = df[df['Total Deaths'] > 0]
    fig = px.box(
        temp, y='Total Deaths', log_y=True, points='all',
        title='Distribution of Fatalities (Log Scale)'
    )
    return fig

def render_death_boxplot_by_type(df):
    # Boxplot par type
    temp = df[df['Total Deaths'] > 0]
    fig = px.box(
        temp, x='Type', y='Total Deaths', log_y=True, points='all',
        title='Fatalities by Volcano Type'
    )
    fig.update_xaxes(tickangle=45)
    return fig

def render_pareto_chart(df):
    # Pareto Chart
    temp = df[['Name', 'Total Deaths']].fillna(0)
    temp = temp[temp['Total Deaths'] > 0].sort_values(by='Total Deaths', ascending=False)
    
    # Calculs
    temp['Cumulative'] = temp['Total Deaths'].cumsum()
    total = temp['Total Deaths'].sum()
    temp['Percentage'] = 100 * temp['Cumulative'] / total
    temp['Rank'] = range(1, len(temp)+1)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=temp['Rank'], y=temp['Total Deaths'], name='Deaths'))
    fig.add_trace(go.Scatter(x=temp['Rank'], y=temp['Percentage'], name='Cumulative %', yaxis='y2', line=dict(color='black')))
    
    fig.update_layout(
        title='Pareto Chart of Fatalities',
        yaxis2=dict(overlaying='y', side='right', range=[0, 105]),
        showlegend=False
    )
    return fig

def render_loglog_heavytail(df):
    # Log-Log Plot pour Power Law
    temp = df[['Total Deaths']].fillna(0)
    temp = temp[temp['Total Deaths'] > 0].sort_values(by='Total Deaths', ascending=False)
    temp['Rank'] = range(1, len(temp)+1)
    
    fig = px.scatter(
        temp, x='Rank', y='Total Deaths',
        log_x=True, log_y=True,
        title='Log-Log Rank-Size Plot (Power Law Check)'
    )
    return fig

def render_correlation_heatmap(df):
    # Heatmap
    cols = ['Total Deaths', 'Total Injuries', 'Total Damage ($Mil)', 'VEI']
    # On garde que ce qui existe dans le df
    existing_cols = [c for c in cols if c in df.columns]
    
    corr = df[existing_cols].corr()
    
    fig = px.imshow(
        corr, text_auto=True, color_continuous_scale='RdBu_r',
        title='Correlation Matrix'
    )
    return fig