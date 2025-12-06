import pandas as pd
import project

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = project.load_data()
lesser_sunda = df[df['Region'] == 'Lesser Sunda Is']
print("Top 10 Deadliest in Lesser Sunda Is (by Deaths):")
print(lesser_sunda.sort_values('Deaths', ascending=False)[['Name', 'Year', 'Deaths', 'Total_Deaths']].head(10))

print("\nTop 10 Deadliest in Lesser Sunda Is (by Total_Deaths):")
print(lesser_sunda.sort_values('Total_Deaths', ascending=False)[['Name', 'Year', 'Deaths', 'Total_Deaths']].head(10))
