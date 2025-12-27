import streamlit as st
import pandas as pd
import numpy as np
import pickle
import json
import plotly.graph_objects as go
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Fair Rent Advisor", page_icon="🏢", layout="centered")

# --- LOAD ARTIFACTS ---
@st.cache_resource
def load_artifacts():
    # Calculate path relative to this script
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    try:
        with open(os.path.join(MODELS_DIR, 'locality_mapping.json'), 'r') as f:
            locality_map = json.load(f)
        
        with open(os.path.join(MODELS_DIR, 'rent_model_artifacts.pkl'), 'rb') as f:
            artifacts = pickle.load(f)
            
        return locality_map, artifacts
    except FileNotFoundError:
        return None, None

locality_map, artifacts = load_artifacts()

if not locality_map or not artifacts:
    st.error("⚠️ System Error: Artifacts are missing. Please run the training script.")
    st.stop()

model = artifacts['model']
locality_value_map = artifacts['locality_value_map']
global_mean_rent = artifacts['global_mean_rent']
feature_columns = artifacts['feature_columns']

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🏠 Fair Rent Advisor</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: grey; margin-top: -10px;'>AI-Powered Valuation for Mumbai, Delhi, Pune</h5>", unsafe_allow_html=True)
st.divider()

# --- INPUT SECTION (Card) ---
with st.container(border=True):
    st.subheader("📝 Property Details")
    st.write("") # Spacer for "bigger" feel
    
    # Row 1: Location
    col1, col2 = st.columns(2)
    with col1:
        city_sel = st.selectbox("City", options=locality_map.keys())
    with col2:
        available_localities = locality_map.get(city_sel, [])
        locality = st.selectbox("Locality", options=available_localities)
    
    st.write("") # Spacer between rows
    
    # Row 2: Specs
    col3, col4 = st.columns(2)
    with col3:
        bhk = st.selectbox("BHK", options=[1, 2, 3, 4, 5])
    with col4:
        furnishing = st.selectbox("Furnishing", options=["Unfurnished", "Semi-Furnished", "Furnished"])
        
    st.write("") # Spacer between rows
        
    # Row 3: Metrics
    col5, col6 = st.columns(2)
    with col5:
        area = st.number_input("Area (sq ft)", min_value=200, max_value=10000, value=1000, step=50)
    with col6:
        owner_ask = st.number_input("Owner Asking Price (₹)", min_value=1000, value=25000, step=1000)
    
    st.write("") # Bottom Spacer
    submitted = st.button("Analyze Fair Rent", type="primary")

# --- RESULTS SECTION ---
if submitted:
    # 1. Prediction Logic
    loc_val = locality_value_map.get(locality, global_mean_rent)
    
    input_df = pd.DataFrame(columns=feature_columns)
    input_df.loc[0] = 0
    input_df.at[0, 'BHK'] = bhk
    input_df.at[0, 'Area'] = area
    input_df.at[0, 'Locality_Value'] = loc_val
    
    city_col = f"city_{city_sel}"
    furnishing_col = f"Furnishing_{furnishing}"
    
    if city_col in feature_columns:
        input_df.at[0, city_col] = 1
    if furnishing_col in feature_columns:
        input_df.at[0, furnishing_col] = 1
        
    pred_log = model.predict(input_df)[0]
    fair_rent = np.expm1(pred_log)
    
    # Range
    rent_low = fair_rent * 0.95
    rent_high = fair_rent * 1.05
    
    st.write("")
    st.markdown("### 📊 Valuation Result")
    st.success(f"**Fair Rent Estimate:** ₹{rent_low:,.0f} - ₹{rent_high:,.0f}")
    
    # 2. Gauge Chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = owner_ask,
        domain = {'x': [0, 1], 'y': [0, 1]},
        delta = {'reference': fair_rent, 'increasing': {'color': "#ef4444"}, 'decreasing': {'color': "#22c55e"}},
        gauge = {
            'axis': {'range': [0, fair_rent * 1.5]},
            'bar': {'color': "rgba(0,0,0,0)"},
            'steps': [
                {'range': [0, fair_rent], 'color': "#dcfce7"},
                {'range': [fair_rent, fair_rent * 1.15], 'color': "#fef9c3"},
                {'range': [fair_rent * 1.15, fair_rent * 1.5], 'color': "#fee2e2"}
            ],
            'threshold': {
                'line': {'color': "#1e293b", 'width': 3},
                'thickness': 0.8,
                'value': owner_ask
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)
