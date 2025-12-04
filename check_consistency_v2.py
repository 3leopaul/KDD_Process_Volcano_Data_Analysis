import pandas as pd

def load_raw_data(filepath):
    try:
        df = pd.read_csv(filepath, sep='\t')
        return df
    except FileNotFoundError:
        return None

df = load_raw_data('volcano-events.tsv')

if df is not None:
    # 1. Tsunami Check (Tsu vs W)
    df['Has_Tsu_Col'] = df['Tsu'].notna()
    df['Has_W_Agent'] = df['Agent'].astype(str).apply(lambda x: 'W' in [a.strip() for a in x.split(',')])
    
    col_but_no_agent = df[df['Has_Tsu_Col'] & ~df['Has_W_Agent']]
    agent_but_no_col = df[~df['Has_Tsu_Col'] & df['Has_W_Agent']]
    
    print(f"Tsunami (Tsu vs W):")
    print(f"  - Has 'Tsu' column but NO 'W' agent: {len(col_but_no_agent)}")
    print(f"  - Has 'W' agent but NO 'Tsu' column: {len(agent_but_no_col)}")
    
    # 2. Earthquake Check (Eq vs S)
    df['Has_Eq_Col'] = df['Eq'].notna()
    df['Has_S_Agent'] = df['Agent'].astype(str).apply(lambda x: 'S' in [a.strip() for a in x.split(',')])
    
    eq_col_but_no_agent = df[df['Has_Eq_Col'] & ~df['Has_S_Agent']]
    eq_agent_but_no_col = df[~df['Has_Eq_Col'] & df['Has_S_Agent']]
    
    print(f"\nEarthquake (Eq vs S):")
    print(f"  - Has 'Eq' column but NO 'S' agent: {len(eq_col_but_no_agent)}")
    print(f"  - Has 'S' agent but NO 'Eq' column: {len(eq_agent_but_no_col)}")
