import pandas as pd

def load_raw_data(filepath):
    try:
        df = pd.read_csv(filepath, sep='\t')
        return df
    except FileNotFoundError:
        return None

df = load_raw_data('volcano-events.tsv')

if df is not None:
    # Clean and explode agents
    df_agents = df.dropna(subset=['Agent']).copy()
    df_agents['Agent_List'] = df_agents['Agent'].apply(lambda x: [agent.strip() for agent in str(x).split(',') if agent.strip()])
    
    # We want to check stats for each unique code
    unique_codes = set([item for sublist in df_agents['Agent_List'] for item in sublist])
    
    stats = []
    for code in unique_codes:
        # Filter rows having this code
        mask = df_agents['Agent_List'].apply(lambda x: code in x)
        count = mask.sum()
        # Use the original df to get deaths for these rows
        # We need to map back to original indices
        indices = df_agents[mask].index
        deaths = df.loc[indices, 'Total Deaths'].sum()
        stats.append({'Code': code, 'Count': count, 'Total_Deaths': deaths})
        
    df_stats = pd.DataFrame(stats).sort_values('Total_Deaths', ascending=False)
    print(df_stats)
