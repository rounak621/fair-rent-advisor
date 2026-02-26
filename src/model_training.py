import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

def train_rent_model_v2():
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'cleaned_rent_data.csv')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    # Load data
    try:
        df = pd.read_csv(DATA_PATH)
        print(f"Data Loaded from {DATA_PATH}: {df.shape}")
    except FileNotFoundError:
        print(f"Error: {DATA_PATH} not found.")
        return

    # --- 1. Filter Extreme Outliers ---
    df = df[df['Rent'] > 1000].copy()
    
    # --- 2. Feature Engineering: Target Encoding for Locality ---
    locality_stats = df.groupby('Locality')['Rent'].mean().to_dict()
    df['Locality_Value'] = df['Locality'].map(locality_stats)
    
    global_mean_rent = df['Rent'].mean()
    df['Locality_Value'].fillna(global_mean_rent, inplace=True)
    
    # Save Locality Map
    locality_dict = {}
    cities = df['city'].unique()
    for city in cities:
        localities = df[df['city'] == city]['Locality'].unique().tolist()
        locality_dict[city] = sorted(localities)
    
    with open(os.path.join(MODELS_DIR, 'locality_mapping.json'), 'w') as f:
        json.dump(locality_dict, f)
        
    # --- 3. Encoding Other Features ---
    df_encoded = pd.get_dummies(df, columns=['city', 'Furnishing'], drop_first=False)
    df_encoded.drop(columns=['Locality'], inplace=True)
    
    feature_columns = [col for col in df_encoded.columns if col != 'Rent']
    
    X = df_encoded.drop(columns=['Rent'])
    y = np.log1p(df_encoded['Rent']) 

    print(f"Training Features: {X.columns.tolist()}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- 4. Gradient Boosting ---
    gbr = GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=5, random_state=42)
    gbr.fit(X_train, y_train)

    # Evaluate
    y_pred_log = gbr.predict(X_test)
    y_pred = np.expm1(y_pred_log)
    y_test_orig = np.expm1(y_test)
    
    r2 = r2_score(y_test_orig, y_pred)
    mae = mean_absolute_error(y_test_orig, y_pred)
    
    print(f"Model V2 Trained. R2 Score: {r2:.4f}, MAE: {mae:.2f}")

    # --- Save Artifacts ---
    artifacts = {
        'model': gbr,
        'locality_value_map': locality_stats,
        'global_mean_rent': global_mean_rent,
        'feature_columns': X.columns.tolist() 
    }

    with open(os.path.join(MODELS_DIR, 'rent_model_artifacts.pkl'), 'wb') as f:
        pickle.dump(artifacts, f)
    print(f"Saved artifacts to {MODELS_DIR}")

if __name__ == "__main__":
    train_rent_model_v2()
