import pandas as pd
import numpy as np
import re
import os

def clean_and_merge_data():
    # File paths - Adjusted for 'src' folder execution context or project root
    # We assume script is run from project root, but for safety lets use relative paths
    # If run from project root: data/raw/...
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

    files = {
        'Delhi': os.path.join(RAW_DIR, 'Indian_housing_Delhi_data.csv'),
        'Mumbai': os.path.join(RAW_DIR, 'Indian_housing_Mumbai_data.csv'),
        'Pune': os.path.join(RAW_DIR, 'Indian_housing_Pune_data.csv')
    }

    dfs = []
    
    for city, filepath in files.items():
        try:
            df = pd.read_csv(filepath)
            df['city'] = city
            dfs.append(df)
            print(f"Loaded {city} data: {df.shape}")
        except FileNotFoundError:
            print(f"Error: {filepath} not found.")
            return

    if not dfs:
        print("No data loaded.")
        return

    # Merge all data
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"Combined Shape: {combined_df.shape}")

    # --- Clean Data ---

    # 1. Extract BHK (integer) from house_type
    def extract_bhk(text):
        if not isinstance(text, str):
            return np.nan
        match = re.search(r'(\d+)\s*BHK', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return np.nan

    combined_df['BHK'] = combined_df['house_type'].apply(extract_bhk)

    # 2. Clean Area (float) from house_size
    def extract_area(text):
        if not isinstance(text, str):
            return np.nan
        clean_text = text.lower().replace('sq ft', '').replace(',', '').strip()
        try:
            return float(clean_text)
        except ValueError:
            return np.nan

    combined_df['Area'] = combined_df['house_size'].apply(extract_area)

    # 3. Rename Columns
    combined_df.rename(columns={
        'price': 'Rent',
        'location': 'Locality',
        'Status': 'Furnishing'
    }, inplace=True)

    # 4. Standardize Rent
    if combined_df['Rent'].dtype == object:
         combined_df['Rent'] = combined_df['Rent'].astype(str).str.replace(',', '').astype(float)
    
    # Drop rows with NaN
    initial_count = len(combined_df)
    combined_df.dropna(subset=['BHK', 'Area', 'Rent'], inplace=True)
    final_count = len(combined_df)
    print(f"Dropped {initial_count - final_count} rows with missing critical data.")

    # Select and Reorder columns
    cols_to_keep = ['city', 'Locality', 'BHK', 'Area', 'Furnishing', 'Rent']
    final_df = combined_df[cols_to_keep]

    # Save to CSV
    output_file = os.path.join(PROCESSED_DIR, 'cleaned_rent_data.csv')
    final_df.to_csv(output_file, index=False)
    print(f"Successfully saved cleaned data to {output_file}")
    print(final_df.head())

if __name__ == "__main__":
    clean_and_merge_data()
