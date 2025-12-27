# AI-Assisted Rental Price Prediction & Fair Rent Advisor

## Overview
This project predicts fair rental prices for properties in Delhi, Mumbai, and Pune using a Gradient Boosting model. It also integrates Google Gemini to provide negotiation advice.

## Project Structure
```
Rental Price Prediction/
├── data/
│   ├── raw/                  # Original CSVs
│   └── processed/            # cleaned_rent_data.csv
├── models/                   # Pickle files, JSON mappings
├── src/                      # Source code
│   ├── data_pipeline.py      # Preprocessing script
│   └── model_training.py     # Training script
├── app/                      # Streamlit app
│   └── main.py              # Main application
├── requirements.txt
└── README.md
```

## Prerequisites
- Python 3.8+

## Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Prepare Data** (Optional if data exists):
    ```bash
    python src/data_pipeline.py
    ```

2.  **Train Model** (Optional if models exist):
    ```bash
    python src/model_training.py
    ```

3.  **Run Application**:
    ```bash
    python -m streamlit run app/main.py
    ```

## Docker

1.  **Build**:
    ```bash
    docker build -t rent-advisor .
    ```

2.  **Run**:
    ```bash
    docker run -p 8501:8501 rent-advisor
    ```
