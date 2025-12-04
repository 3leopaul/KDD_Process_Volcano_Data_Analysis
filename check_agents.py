import pandas as pd

def load_raw_data(filepath):
    try:
        df = pd.read_csv(filepath, sep='\t')
        return df
    except FileNotFoundError:
        return None

df = load_raw_data('volcano-events.tsv')
if df is not None:
    agents = df['Agent'].dropna().unique()
    print("Unique Agents:", agents)
    
    # Split and find all unique codes
    all_codes = set()
    for a in agents:
        for code in str(a).split(','):
            all_codes.add(code.strip())
    print("Unique Codes:", sorted(list(all_codes)))
