import pandas as pd

def load_raw_data(filepath):
    try:
        df = pd.read_csv(filepath, sep='\t')
        return df
    except FileNotFoundError:
        return None

df = load_raw_data('volcano-events.tsv')

if df is not None:
    # Rename for consistency with project.py if needed, or just use raw names
    # Raw names: 'Tsu', 'Eq', 'Agent'
    
    print(f"Total rows: {len(df)}")
    
    # Check Tsunami (Tsu) vs Agent 'W' (Waves/Tsunami) or 'T' (Tephra)?
    # Wait, earlier analysis showed 'W' = Waves (Tsunami) and 'T' = Tephra (Ash).
    # The user asked: "check if the columns Tsunami and Earthquake repeat the values of the corresponding letters in the agent column."
    # I need to be careful about which letter corresponds to which.
    # Based on my previous mapping: 'W': 'Waves (Tsunami)', 'T': 'Tephra (Ash)'.
    # So 'Tsu' column should match 'W' in Agent, NOT 'T'.
    # And 'Eq' column should match 'E' (Electrical?) or 'S' (Seismic)?
    # Let's re-verify the mapping.
    # Previous mapping: 'S': 'Seismic', 'E': 'Electrical'.
    # Usually 'Eq' implies Seismic.
    
    # Let's check the data to see what correlates.
    
    # 1. Tsunami Check
    # 'Tsu' column vs 'W' in Agent
    df['Has_Tsu_Col'] = df['Tsu'].notna()
    df['Has_W_Agent'] = df['Agent'].astype(str).apply(lambda x: 'W' in [a.strip() for a in x.split(',')])
    
    mismatch_tsu = df[df['Has_Tsu_Col'] != df['Has_W_Agent']]
    print(f"\nMismatch between 'Tsu' column and 'W' (Tsunami) in Agent: {len(mismatch_tsu)} rows")
    if len(mismatch_tsu) > 0:
        print(mismatch_tsu[['Name', 'Year', 'Tsu', 'Agent']].head(10))

    # 'Tsu' column vs 'T' in Agent (Just in case user meant T for Tsunami, though T is usually Tephra)
    df['Has_T_Agent'] = df['Agent'].astype(str).apply(lambda x: 'T' in [a.strip() for a in x.split(',')])
    mismatch_tsu_T = df[df['Has_Tsu_Col'] != df['Has_T_Agent']]
    print(f"\nMismatch between 'Tsu' column and 'T' (Tephra?) in Agent: {len(mismatch_tsu_T)} rows")


    # 2. Earthquake Check
    # 'Eq' column vs 'S' (Seismic) in Agent
    df['Has_Eq_Col'] = df['Eq'].notna()
    df['Has_S_Agent'] = df['Agent'].astype(str).apply(lambda x: 'S' in [a.strip() for a in x.split(',')])
    
    mismatch_eq_S = df[df['Has_Eq_Col'] != df['Has_S_Agent']]
    print(f"\nMismatch between 'Eq' column and 'S' (Seismic) in Agent: {len(mismatch_eq_S)} rows")
    
    # 'Eq' column vs 'E' (Electrical?) in Agent
    df['Has_E_Agent'] = df['Agent'].astype(str).apply(lambda x: 'E' in [a.strip() for a in x.split(',')])
    mismatch_eq_E = df[df['Has_Eq_Col'] != df['Has_E_Agent']]
    print(f"\nMismatch between 'Eq' column and 'E' in Agent: {len(mismatch_eq_E)} rows")

