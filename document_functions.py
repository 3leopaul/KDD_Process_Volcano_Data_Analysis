
import json
import re

# Dictionary mapping function names to their NEW, fully commented source code
# The source code must be a LIST of strings, including newlines, exactly as it appears in the notebook source list (normally)
# But for simplicity, we'll write them as strings here and split them later.
functions = {}

functions['process_tsu_eq_columns'] = """def process_tsu_eq_columns(df):
    \"\"\"
    Replaces NaN values with 0 and non-NaN values with 1 in the 'Tsu' and 'Eq' columns.
    
    input: df (pd.DataFrame)
    output: df_processed (pd.DataFrame)
    \"\"\"
    # Create a copy to ensure we don't modify the original dataframe in place
    df_processed = df.copy()
    
    # Iterate over the two target columns: Tsunami (Tsu) and Earthquake (Eq)
    for col in ['Tsu', 'Eq']:
        # Check if the column exists to prevent errors
        if col in df_processed.columns:
            # Convert non-null values to 1 (True) and null values to 0 (False)
            # This standardizes these columns into binary indicators
            df_processed[col] = df_processed[col].notna().astype(int)
            
    return df_processed
"""

functions['show_missing_data'] = """def show_missing_data(df):
    \"\"\"
    Calculates and prints the number of missing values per column.
    
    input: df (pd.DataFrame)
    output: None
    \"\"\"
    # Calculate the sum of null values for each column in the dataframe
    missing_values = df.isnull().sum()
    
    # Filter the Series to show ONLY columns that have at least one missing value (> 0)
    missing_only = missing_values[missing_values > 0]
    
    print("Missing Data Points per Column:")
    # Check if there are any missing values to report
    if not missing_only.empty:
        # Print the relevant columns and their missing count
        print(missing_only)
    else:
        # Feedback if dataset is fully populated
        print("No missing values found in the dataset columns.")
"""

functions['impute_missing_numericals'] = """def impute_missing_numericals(df):
    \"\"\"
    Imputes missing values for ALL quantitative columns (Deaths, Injuries, Damage, etc.)
    based on their corresponding Description columns using the Median strategy.
    
    input: df (pd.DataFrame)
    output: df_imputed (pd.DataFrame)
    \"\"\"

    # Create a copy of the dataframe to perform imputation without affecting the original data
    df_imputed = df.copy()
    
    # Define pairs of (Quantitative Column, Description Column) to process
    pairs = [
        ('Deaths', 'Death Description'),
        ('Missing', 'Missing Description'),
        ('Injuries', 'Injuries Description'),
        ('Damage ($Mil)', 'Damage Description'),
        ('Houses Destroyed', 'Houses Destroyed Description'),
        ('Total Deaths', 'Total Death Description'),
        ('Total Missing', 'Total Missing Description'),
        ('Total Injuries', 'Total Injuries Description'),
        ('Total Damage ($Mil)', 'Total Damage Description'),
        ('Total Houses Destroyed', 'Total Houses Destroyed Description')
    ]
    
    print("--- Imputation Report ---")
    
    # Iterate through each pair to apply imputation logic
    for qty_col, desc_col in pairs:
        # Verify both columns exist in validity check
        if qty_col not in df_imputed.columns or desc_col not in df_imputed.columns:
            continue
            
        # 1. Calculate Medians for each description category (1, 2, 3, 4) dynamically
        # Group by the description column and find the median of the quantitative values
        median_map = df_imputed.groupby(desc_col)[qty_col].median()
        
        # 2. Identify rows that need imputation:
        # The quantitative value is NaN BUT the description (category) is known (not NaN)
        mask = df_imputed[qty_col].isna() & df_imputed[desc_col].notna()
        
        # Count how many rows will be affected
        count_to_fill = mask.sum()
        
        if count_to_fill > 0:
            # 3. Apply Imputation
            # Use the 'map' function to look up the median value for each row's description category
            # and assign it to the quantitative column where the mask is True
            df_imputed.loc[mask, qty_col] = df_imputed.loc[mask, desc_col].map(median_map)
            
            print(f"[{qty_col}] Filled {count_to_fill} missing values using calculated medians: {median_map.to_dict()}")
        else:
            print(f"[{qty_col}] No imputable missing values found.")

    return df_imputed
"""

functions['impute_description_ordinal_scales'] = """def impute_description_ordinal_scales(df):
    \"\"\"
    Imputes missing Description values (Category 1.0, 2.0, 3.0, 4.0) based on the 
    corresponding known Quantitative values using geometric midpoints as thresholds.
    
    input: df (pd.DataFrame)
    output: df_imputed (pd.DataFrame)
    \"\"\"
    # Create a copy of the dataframe
    df_imputed = df.copy()
    
    # Define pairs to process
    pairs = [
        ('Deaths', 'Death Description'),
        ('Missing', 'Missing Description'),
        ('Injuries', 'Injuries Description'),
        ('Damage ($Mil)', 'Damage Description'),
        ('Houses Destroyed', 'Houses Destroyed Description'),
        ('Total Deaths', 'Total Death Description'),
        ('Total Missing', 'Total Missing Description'),
        ('Total Injuries', 'Total Injuries Description'),
        ('Total Damage ($Mil)', 'Total Damage Description'),
        ('Total Houses Destroyed', 'Total Houses Destroyed Description')
    ]
    
    print("--- Description Imputation Report ---")
    
    for qty_col, desc_col in pairs:
        # Check column existence
        if qty_col not in df_imputed.columns or desc_col not in df_imputed.columns:
            continue
            
        # 1. Get medians for existing categories to understand the scale
        medians = df_imputed.groupby(desc_col)[qty_col].median().sort_index()
        
        # Need at least 2 categories to calculate a threshold between them
        if len(medians) < 2:
            print(f"[{desc_col}] Not enough categories to build thresholds. Skipping.")
            continue
            
        # 2. Build Thresholds (Geometric Midpoints)
        # We calculate the cutoff point between category N and N+1
        thresholds = []
        cats = medians.index.tolist()
        
        for i in range(len(cats) - 1):
            c1 = cats[i]
            c2 = cats[i+1]
            m1 = medians[c1]
            m2 = medians[c2]
            
            # Handle edge case of 0 values to avoid math errors in geometric mean
            if m1 <= 0: m1 = 0.01
            if m2 <= 0: m2 = 0.01
            
            # Geometric mean represents a balanced threshold for logarithmic-like scales
            limit = np.sqrt(m1 * m2)
            thresholds.append((limit, c1))
            
        last_cat = cats[-1]
        
        # 3. Apply Imputation
        # Find rows where Quantity is Known (notna) but Description is Missing (isna)
        mask = df_imputed[qty_col].notna() & df_imputed[desc_col].isna()
        target_indices = df_imputed[mask].index
        
        count = 0
        for idx in target_indices:
            val = df_imputed.at[idx, qty_col]
            assigned_cat = last_cat
            
            # Check which interval the value falls into
            for limit, cat in thresholds:
                if val <= limit:
                    assigned_cat = cat
                    break
            
            # Assign the determined category (as float to verify consistency)
            df_imputed.at[idx, desc_col] = float(assigned_cat)
            count += 1
            
        if count > 0:
            print(f"[{desc_col}] Imputed {count} missing descriptions based on numeric values.")
    
    return df_imputed
"""

functions['analyze_information_loss'] = """def analyze_information_loss(df):
    \"\"\"
    Analyzes and prints a report on missing data for quantitative vs description columns.
    
    input: df (pd.DataFrame)
    output: None
    \"\"\"
    # Define the pairs to analyze
    pairs = [
        ('Deaths', 'Death Description'),
        ('Missing', 'Missing Description'),
        ('Injuries', 'Injuries Description'),
        ('Damage ($Mil)', 'Damage Description'),
        ('Houses Destroyed', 'Houses Destroyed Description'),
        ('Total Deaths', 'Total Death Description'),
        ('Total Missing', 'Total Missing Description'),
        ('Total Injuries', 'Total Injuries Description'),
        ('Total Damage ($Mil)', 'Total Damage Description'),
        ('Total Houses Destroyed', 'Total Houses Destroyed Description')
    ]
    
    print(f"{'Quantitative Column':<25} | {'Missing Qty':<12} | {'Description Col':<30} | {'Hidden Data (Loss)':<20} | {'Missing Desc'}")
    print("-" * 120)
    
    for qty_col, desc_col in pairs:
        if qty_col in df.columns and desc_col in df.columns:
            # Count missing values in quantitative column
            missing_qty = df[qty_col].isna().sum()
            # Count missing values in description column
            missing_desc = df[desc_col].isna().sum()
            
            # "Hidden Data" or "Information Loss":
            # Rows where Description exists (we know the category) but Quantitative is NaN (we lost the exact number)
            # This represents data that can be recovered/imputed
            loss_mask = df[desc_col].notna() & df[qty_col].isna()
            hidden_data_count = loss_mask.sum()
            
            print(f"{qty_col:<25} | {missing_qty:<12} | {desc_col:<30} | {hidden_data_count:<20} | {missing_desc}")
"""

functions['plot_eruption_comparison_curves'] = """def plot_eruption_comparison_curves(df: pd.DataFrame):
    \"\"\"
    Plots KDE curves comparing the distribution of 'Total Deaths' and 'Deaths'
    for eruptions with <= 500 total deaths to visualize discrepancies.

    input: df (pd.DataFrame)
    output: None
    \"\"\"
    # Filter for eruptions with small but non-zero death tolls for clearer visualization
    df_filtered = df[(df['Total Deaths'] > 0) & (df['Total Deaths'] <= 500)].copy()
    
    plt.figure(figsize=(10, 6))
    # Plot KDE for Total Deaths
    sns.kdeplot(data=df_filtered, x='Total Deaths', label='Total Deaths', fill=True, alpha=0.5)
    # Plot KDE for Normal Deaths (direct deaths)
    sns.kdeplot(data=df_filtered, x='Deaths', label='Normal Deaths', fill=True, alpha=0.5)
    
    plt.title('Comparison of Total Deaths vs Normal Deaths (<= 500)')
    plt.xlabel('Number of Deaths')
    plt.ylabel('Density')
    plt.legend()
    plt.show()
"""

functions['process_total_normal_data'] = """def process_total_normal_data(df):
    \"\"\"
    Calculates the difference between 'Total Deaths' and 'Deaths', identifies discrepancies,
    and prints statistics about these differences.

    input: df (pd.DataFrame)
    output: df (pd.DataFrame) - with added 'Diff Deaths' column
    \"\"\"
    print("\\n=== Processing Total vs Normal Data ===")
    
    # Calculate 'Diff Deaths' as the discrepancy between Total and Direct deaths
    df['Diff Deaths'] = df['Total Deaths'] - df['Deaths']
    
    # Identify rows where there IS a difference (discrepancy)
    diff_deaths_rows = df[df['Diff Deaths'] != 0]
    print(f"Number of rows where 'Total Deaths' != 'Deaths': {len(diff_deaths_rows)}")
    
    if len(diff_deaths_rows) > 0:
        print("Sample rows with differences:")
        print(diff_deaths_rows[['Total Deaths', 'Deaths', 'Diff Deaths']].head())
    else:
        print("No differences found between 'Total Deaths' and 'Deaths'.")
        
    # Analyze distribution of the differences to understand the scale of "indirect" deaths
    print("\\nStatistics for 'Diff Deaths' (where non-zero):")
    print(diff_deaths_rows['Diff Deaths'].describe())
    
    return df
"""

functions['check_description_values'] = """def check_description_values(df):
    \"\"\"
    Iterates through all 'Description' columns and prints their unique values
    to verify the ordinal scales (1-4) or identify anomalies.

    input: df (pd.DataFrame)
    output: None
    \"\"\"
    print("\\n=== Checking Description Values ===")
    
    # Find all columns containing 'Description' in their name
    description_cols = [col for col in df.columns if 'Description' in col]
    
    for col in description_cols:
        unique_vals = df[col].unique()
        print(f"Unique values in '{col}': {unique_vals}")
        
        # Warn if there are too many unique values, suggesting potential data issues
        if len(unique_vals) > 10:
             print(f"  Note: Many unique values ({len(unique_vals)}).")
"""

functions['load_raw_data'] = """def load_raw_data(filepath):
    \"\"\"
    Reads the TSV file into a pandas DataFrame.
    
    input: filepath (str) - Path to the TSV file.
    output: df (pd.DataFrame) or None - Loaded dataframe or None if file not found.
    \"\"\"
    try:
        df = pd.read_csv(filepath, sep='\\t')
        print("File loaded.")
        return df
    except FileNotFoundError:
        print("File not found. Please check the path.")
        return None
"""

functions['divide_agents'] = """def divide_agents(df):
    \"\"\"
    Splits the comma-separated 'Agent' column into individual binary columns (Agent_P, Agent_T, etc.).
    
    input: df (pd.DataFrame)
    output: df_agent_divided (pd.DataFrame) - Dataframe with new binary agent columns.
    \"\"\"
    # Convert to string, handle NaNs as empty strings, and remove spaces (e.g. "T, m" -> "T,m")
    agents_cleaned = df['Agent'].fillna('').astype(str).str.replace(' ', '')
    
    # We Split and Create the Binary Columns
    # 'sep=,' tells pandas to treat comma as the delimiter
    agent_dummies = agents_cleaned.str.get_dummies(sep=',')
    
    # Rename columns for clarity (e.g. "P" -> "Agent_P")
    agent_dummies = agent_dummies.add_prefix('Agent_')
    
    # Concatenate the new columns to the original dataframe
    df_agent_divided = pd.concat([df, agent_dummies], axis=1)

    df_agent_divided = df_agent_divided.drop(columns=['Agent'])
    
    return df_agent_divided
"""

functions['check_tsu_eq_consistency'] = """def check_tsu_eq_consistency(df_agent_divided):
    \"\"\"
    Checks for consistency between specific Agent flags (W for Waves, S for Seismic) 
    and their corresponding standalone columns (Tsu, Eq).
    Also checks overlap between Tsunami and Flood agents.
    
    input: df_agent_divided (pd.DataFrame)
    output: None
    \"\"\"
    # We count the number of non-null values in the 'Tsu' and 'Eq' columns
    tsu_col_count = df_agent_divided['Tsu'].notna().sum()
    eq_col_count = df_agent_divided['Eq'].notna().sum()

    # We count the number of 'T', 'S', 'W', and 'F' codes in the 'Agent' column
    agent_S_col_count = df_agent_divided['Agent_S'].sum()
    agent_W_col_count = df_agent_divided['Agent_W'].sum()
    agent_F_col_count = df_agent_divided['Agent_F'].sum() # Added Flood count

    # Print the counts
    print(f"\\nCOUNTS:")
    print(f"Total non-null 'Tsu' column values: {tsu_col_count}")
    print(f"Total 'W' (Waves) codes in Agent:   {agent_W_col_count}")
    print(f"Total 'F' (Floods) codes in Agent:  {agent_F_col_count}\\n")

    print(f"Total non-null 'Eq' column values:  {eq_col_count}")
    print(f"Total 'S' (Seismic) codes in Agent: {agent_S_col_count}\\n")

    # Now we check if the columns match
    print(f"\\nCONSISTENCY CHECK:")
    
    # Check Tsunami (Agent_W vs Tsu) 
    mismatch_tsu_A = df_agent_divided[df_agent_divided['Tsu'].notna() & (df_agent_divided['Agent_W'] == 0)]
    mismatch_tsu_B = df_agent_divided[(df_agent_divided['Agent_W'] == 1) & df_agent_divided['Tsu'].isna()]

    if mismatch_tsu_A.empty and mismatch_tsu_B.empty:
        print("Tsunami Data (Agent_W): The data is consistent.")
        print(" Every row with a Tsunami flag (W) has a corresponding 'Tsu' data and vice versa.")
    else:
        print("Tsunami Data (Agent_W): The data is not consistent.")
        if not mismatch_tsu_A.empty:
            print(f"   - {len(mismatch_tsu_A)} rows have 'Tsu' data but are missing the 'W' agent.")
        if not mismatch_tsu_B.empty:
            print(f"   - {len(mismatch_tsu_B)} rows have 'W' agent but are missing 'Tsu' data.")

    # Check Flood (Agent_F vs Tsu)
    mismatch_flood_tsu_A = df_agent_divided[df_agent_divided['Tsu'].notna() & (df_agent_divided['Agent_F'] == 0)]
    mismatch_flood_tsu_B = df_agent_divided[(df_agent_divided['Agent_F'] == 1) & df_agent_divided['Tsu'].isna()]

    print(f"\\n")
    if mismatch_flood_tsu_A.empty and mismatch_flood_tsu_B.empty:
        print("Flood Data (Agent_F) vs Tsunami Data (Tsu): The data is consistent.")
        print(" Every row with a Flood flag (F) has corresponding 'Tsu' data and vice versa.")
    else:
        print("Flood Data (Agent_F) vs Tsunami Data (Tsu): The data is not consistent.")
        if not mismatch_flood_tsu_A.empty:
            print(f"   - {len(mismatch_flood_tsu_A)} rows have 'Tsu' data but are missing the 'F' agent.")
        if not mismatch_flood_tsu_B.empty:
            print(f"   - {len(mismatch_flood_tsu_B)} rows have 'F' agent but are missing 'Tsu' data.")

    # Check Earthquake (Agent_S vs Eq) 
    mismatch_eq_A = df_agent_divided[df_agent_divided['Eq'].notna() & (df_agent_divided['Agent_S'] == 0)]
    mismatch_eq_B = df_agent_divided[(df_agent_divided['Agent_S'] == 1) & df_agent_divided['Eq'].isna()]

    print(f"\\n")
    if mismatch_eq_A.empty and mismatch_eq_B.empty:
        print("Earthquake Data: The data is consistent.")
        print(" Every row with an Earthquake flag has a corresponding 'S' agent and vice versa.")
    else:
        print("Earthquake Data: The data is not consistent.")
        if not mismatch_eq_A.empty:
            print(f"   - {len(mismatch_eq_A)} rows have 'Eq' data but are missing the 'S' agent.")
        if not mismatch_eq_B.empty:
            print(f"   - {len(mismatch_eq_B)} rows have 'S' agent but are missing 'Eq' data.")
"""

functions['show_structure'] = """def show_structure(df):
    \"\"\"
    Prints the shape (rows, columns) and data types of the dataframe.
    
    input: df (pd.DataFrame)
    output: None
    \"\"\" 
    rows, cols = df.shape
    print(f"Number of Rows: {rows}")
    print(f"Number of Columns: {cols}")
 
    print("Data Types:")
    print(df.dtypes)
"""

functions['analyze_total_vs_normal'] = """def analyze_total_vs_normal(df):
    \"\"\"
    Analyzes the relationship between 'Normal' columns (e.g. Deaths) and 'Total' columns (e.g. Total Deaths),
    reporting counts of consistencies, inconsistencies, and anomalies.
    Also compares Description columns.
    
    input: df (pd.DataFrame)
    output: None
    \"\"\"
    numerical_pairs = [
        ('Deaths', 'Total Deaths'),
        ('Missing', 'Total Missing'),
        ('Injuries', 'Total Injuries'),
        ('Damage ($Mil)', 'Total Damage ($Mil)'),
        ('Houses Destroyed', 'Total Houses Destroyed')
    ]

    definition_pairs = [
        ('Death Description', 'Total Death Description'),
        ('Missing Description', 'Total Missing Description'),
        ('Injuries Description', 'Total Injuries Description'),
        ('Damage Description', 'Total Damage Description'),
        ('Houses Destroyed Description', 'Total Houses Destroyed Description')
    ]

    print("--- Numerical Column Comparison ---")
    numerical_headers = [
        'Normal Column', 'Total Column', 'Both Present',
        'Normal == Total', 'Normal < Total', 'Normal > Total (Anomaly)'
    ]
    print(f"{numerical_headers[0]:<20} | {numerical_headers[1]:<25} | {numerical_headers[2]:<15} | {numerical_headers[3]:<18} | {numerical_headers[4]:<18} | {numerical_headers[5]}")
    print("-" * 140)

    for normal_col, total_col in numerical_pairs:
        if normal_col not in df.columns or total_col not in df.columns:
            print(f"{normal_col:<20} | {total_col:<25} | {'N/A':<15} | {'N/A':<18} | {'N/A':<18} | {'N/A'} (Columns not found)")
            continue

        # Filter to rows where both values are present
        both_present_df = df.dropna(subset=[normal_col, total_col])
        count_both_present = len(both_present_df)

        if count_both_present == 0:
            print(f"{normal_col:<20} | {total_col:<25} | {count_both_present:<15} | {'N/A':<18} | {'N/A':<18} | {'N/A'}")
            continue

        # Detailed analysis of relationships
        count_normal_eq_total = (both_present_df[normal_col] == both_present_df[total_col]).sum()
        count_normal_lt_total = (both_present_df[normal_col] < both_present_df[total_col]).sum()
        count_normal_gt_total = (both_present_df[normal_col] > both_present_df[total_col]).sum() # This indicates an anomaly

        print(
            f"{normal_col:<20} | {total_col:<25} | {count_both_present:<15} | "
            f"{count_normal_eq_total:<18} | {count_normal_lt_total:<18} | {count_normal_gt_total}"
        )

    print("\\n--- Description Column Comparison ---")
    definition_headers = [
        'Normal Description', 'Total Description', 'Both Present',
        'Identical', 'Normal < Total', 'Normal > Total (Anomaly)'
    ]
    print(f"{definition_headers[0]:<25} | {definition_headers[1]:<30} | {definition_headers[2]:<15} | {definition_headers[3]:<15} | {definition_headers[4]:<15} | {definition_headers[5]}")
    print("-" * 140)

    for normal_def_col, total_def_col in definition_pairs:
        if normal_def_col not in df.columns or total_def_col not in df.columns:
            print(f"{normal_def_col:<25} | {total_def_col:<30} | {'N/A':<15} | {'N/A':<15} | {'N/A':<15} | {'N/A'} (Columns not found)")
            continue

        # Filter to rows where both values are present (and not NaN)
        both_present_df = df.dropna(subset=[normal_def_col, total_def_col])
        count_both_present = len(both_present_df)

        if count_both_present == 0:
            print(f"{normal_def_col:<25} | {total_def_col:<30} | {count_both_present:<15} | {'N/A':<15} | {'N/A':<15} | {'N/A'}")
            continue

        # Detailed analysis of relationships for definitions using lexicographical comparison
        count_identical = (both_present_df[normal_def_col] == both_present_df[total_def_col]).sum()
        count_normal_lt_total_desc = (both_present_df[normal_def_col] < both_present_df[total_def_col]).sum()
        count_normal_gt_total_desc = (both_present_df[normal_def_col] > both_present_df[total_def_col]).sum()

        print(
            f"{normal_def_col:<25} | {total_def_col:<30} | {count_both_present:<15} | "
            f"{count_identical:<15} | {count_normal_lt_total_desc:<15} | {count_normal_gt_total_desc}"
        )
"""

functions['clean_data'] = """def clean_data(df):
    \"\"\"
    Executes the full cleaning pipeline: drops metadata, divides agents, processes total vs normal deaths,
    imputes missing values, and renames columns for clarity.
    
    input: df (pd.DataFrame) - The raw dataframe
    output: df (pd.DataFrame) - The fully cleaned and preprocessed dataframe
    \"\"\"

    df = df.drop('Search Parameters', axis=1)
    df = df.iloc[1:]
    df = divide_agents(df)
    df = process_total_normal_data(df)
    df = impute_missing_numericals(df)
    df = impute_description_ordinal_scales(df)
    df = process_tsu_eq_columns(df)
    
    #Rename columns to remove spaces and special characters for easier coding 
    #and for a better understanding
    df = df.rename(columns={
        'Mo': 'Month',
        'Dy': 'Day',
        'Tsu': 'Tsunami',
        'Eq': 'Earthquake',
        'Damage ($Mil)': 'Damage_Millions',
        'Elevation (m)': 'Elevation',
        'Houses Destroyed': 'Houses_Destroyed',
        'Injuries Description': 'Injuries_Description',
        'Death Description': 'Deaths_Description',
        'Damage Description': 'Damage_Description',
        'Missing Description': 'Missing_Description',
        'Houses Destroyed Description': 'Houses_Destroyed_Description'
    })

    return df
"""

functions['show_rankings'] = """def show_rankings(df):
    \"\"\"
    Calculates and prints the correlation of numerical variables with 'Deaths', sorted in descending order.
    
    input: df (pd.DataFrame)
    output: None
    \"\"\"
    #We select only numeric columns for correlation analysis
    numeric_df = df.select_dtypes(include=[np.number])

    corr_matrix = numeric_df.corr()

    #Let's see what correlates most strongly with Deaths
    if 'Deaths' in corr_matrix.columns:
        print("Ranking of variables correlated with 'Deaths':")
        print(corr_matrix['Deaths'].sort_values(ascending=False))
"""

def update_notebook_functions(notebook_path, functions_dict):
    print(f"Opening notebook: {notebook_path}")
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    updated_count = 0
    
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source_lines = cell['source']
            if not source_lines: continue
            
            # Combine lines to check the definition
            full_source = "".join(source_lines)
            
            # Regex to find function name
            match = re.match(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', full_source)
            if match:
                func_name = match.group(1)
                #print(f"Found function: {func_name}")
                if func_name in functions_dict:
                    # Get the new code
                    new_code = functions_dict[func_name]
                    
                    # Split into lines creating the list of strings format notebook expects
                    # Use splitlines(keepends=True) to preserve existing newlines
                    new_source_lines = new_code.splitlines(keepends=True)
                    
                    # Ensure the last line ends with newline if consistent with other cells
                    if new_source_lines and not new_source_lines[-1].endswith('\n'):
                        new_source_lines[-1] += '\n'
                            
                    cell['source'] = new_source_lines
                    updated_count += 1
                    print(f"Updated function: {func_name}")

    print(f"Saving notebook... Total functions updated: {updated_count}")
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

if __name__ == "__main__":
    update_notebook_functions('main.ipynb', functions)


