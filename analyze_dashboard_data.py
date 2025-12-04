import pandas as pd
import numpy as np

def load_raw_data(filepath):
    try:
        df = pd.read_csv(filepath, sep='\t')
        return df
    except FileNotFoundError:
        return None

df = load_raw_data('volcano-events.tsv')

if df is not None:
    print("=== 1. Pareto Principle (Countries) ===")
    total_deaths = df['Total Deaths'].sum()
    df_country = df.groupby('Country')['Total Deaths'].sum().sort_values(ascending=False)
    top_10_deaths = df_country.head(10).sum()
    print(f"Total Deaths: {total_deaths}")
    print(f"Top 10 Countries Deaths: {top_10_deaths}")
    print(f"Percentage: {top_10_deaths / total_deaths * 100:.2f}%")
    print("Top 3 Countries:")
    print(df_country.head(3))
    
    print("\n=== 2. Secondary Hazards (Tsunami/Earthquake) ===")
    # Tsunami
    tsu_deaths = df[df['Tsu'].notna()]['Total Deaths'].sum()
    no_tsu_deaths = df[df['Tsu'].isna()]['Total Deaths'].sum()
    print(f"Deaths with Tsunami: {tsu_deaths} vs Without: {no_tsu_deaths}")
    
    # Earthquake
    eq_deaths = df[df['Eq'].notna()]['Total Deaths'].sum()
    no_eq_deaths = df[df['Eq'].isna()]['Total Deaths'].sum()
    print(f"Deaths with Earthquake: {eq_deaths} vs Without: {no_eq_deaths}")
    
    print("\n=== 3. Agent Analysis (Top Killers) ===")
    # We need to map agents first
    df_agents = df.dropna(subset=['Agent']).copy()
    df_agents['Agent_List'] = df_agents['Agent'].apply(lambda x: [agent.strip() for agent in str(x).split(',') if agent.strip()])
    
    hazard_map = {
        'P': 'Pyroclastic Flow', 'M': 'Mudflow', 'T': 'Tephra', 'W': 'Tsunami', 'L': 'Lava Flow',
        'G': 'Gas', 'I': 'Indirect', 'A': 'Avalanche', 'F': 'Floods', 'S': 'Seismic', 'E': 'Electrical'
    }
    
    agent_stats = []
    for code, name in hazard_map.items():
        mask = df_agents['Agent_List'].apply(lambda x: code in x)
        deaths = df.loc[mask.index[mask], 'Total Deaths'].sum()
        count = mask.sum()
        agent_stats.append({'Agent': name, 'Deaths': deaths, 'Count': count})
        
    df_agent_stats = pd.DataFrame(agent_stats).sort_values('Deaths', ascending=False)
    print(df_agent_stats)
    
    print("\n=== 4. Volcano Type vs Impact ===")
    type_stats = df.groupby('Type')['Total Deaths'].sum().sort_values(ascending=False)
    print(type_stats.head(5))
    
    print("\n=== 5. Deaths per Eruption (Rate) ===")
    type_counts = df['Type'].value_counts()
    type_rate = (type_stats / type_counts).sort_values(ascending=False)
    print(type_rate.head(5))

