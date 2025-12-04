import pandas as pd

def load_raw_data(filepath):
    try:
        df = pd.read_csv(filepath, sep='\t')
        return df
    except FileNotFoundError:
        return None

df = load_raw_data('volcano-events.tsv')

if df is not None:
    print("Data Types:")
    print(df[['Tsu', 'Eq', 'Total Deaths']].dtypes)
    print("\nSample Values (Tsu, Eq, Total Deaths):")
    print(df[['Tsu', 'Eq', 'Total Deaths']].dropna(subset=['Tsu', 'Eq'], how='all').head(10))
