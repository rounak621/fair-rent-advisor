# AI-Assisted Rental Price Prediction & Fair Rent Advisor

## Overview
This project predicts fair rental prices for properties in Delhi, Mumbai, and Pune using a Random Forest model. It also integrates Google Gemini to provide negotiation advice based on the predicted fair rent versus the owner's asking price.

## Project Structure
- `preprocess_data.py`: Merges and cleans the raw CSV data.
- `train_model.py`: Trains the machine learning model and saves artifacts.
- `app.py`: The main Streamlit web application.
- `requirements.txt`: List of Python dependencies.

## Prerequisites
- Python 3.8+
- A Google Gemini API Key

## Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Prepare Data**:
    (Skip if `cleaned_rent_data.csv` already exists)
    ```bash
    python preprocess_data.py
    ```

2.  **Train Model**:
    (Skip if `rent_model_artifacts.pkl` and `locality_mapping.json` already exist)
    ```bash
    python train_model.py
    ```

3.  **Run Application**:
    ```bash
    python -m streamlit run app.py
    ```

4.  **Using the App**:
    - The app will open in your browser (usually at `http://localhost:8501`).
    - Enter your **Gemini API Key** in the sidebar to enable the negotiation advice feature.
    - Select City, Locality, and other property details to get a prediction.
