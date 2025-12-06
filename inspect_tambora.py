import pandas as pd
import project

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = project.load_data()
tambora = df[df['Name'] == 'Tambora']
print("Tambora Data:")
for index, row in tambora.iterrows():
    print(f"Index: {index}")
    print(f"Year: {row['Year']}")
    print(f"Deaths: {row['Deaths']}")
    print(f"Total_Deaths: {row['Total_Deaths']}")
    print(f"Country: {row['Country']}")
    print(f"Region: {row['Region']}")
    print("-" * 20)
