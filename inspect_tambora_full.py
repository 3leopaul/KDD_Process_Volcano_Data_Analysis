import pandas as pd
import project

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = project.load_data()
tambora = df[df['Name'] == 'Tambora']
print("Tambora Data (All Columns):")
for index, row in tambora.iterrows():
    for col in df.columns:
        print(f"{col}: {row[col]}")
