from flask import Flask, render_template, request, jsonify
import pickle, json, os
import numpy as np
import pandas as pd
from Ai.apiCall import get_real_estate_advice

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

with open(os.path.join(MODELS_DIR, "locality_mapping.json"), "r") as f:
    locality_map = json.load(f)

with open(os.path.join(MODELS_DIR, "rent_model_artifacts.pkl"), "rb") as f:
    artifacts = pickle.load(f)

model = artifacts['model']
locality_value_map = artifacts['locality_value_map']
global_mean_rent = artifacts['global_mean_rent']
feature_columns = artifacts['feature_columns']

@app.route('/')
def home():
    return render_template("index.html", cities=list(locality_map.keys()), cities_map=locality_map)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    city = data['city']
    locality = data['locality']
    bhk = int(data['bhk'])
    area = float(data['area'])
    furnishing = data['furnishing']

    loc_val = float(locality_value_map.get(locality, global_mean_rent))
    input_df = pd.DataFrame(columns=feature_columns)
    input_df.loc[0] = 0
    input_df.at[0,'BHK'] = bhk
    input_df.at[0,'Area'] = area
    input_df.at[0,'Locality_Value'] = loc_val

    city_col = f"city_{city}"
    furnishing_col = f"Furnishing_{furnishing}"
    if city_col in feature_columns: input_df.at[0, city_col] = 1
    if furnishing_col in feature_columns: input_df.at[0, furnishing_col] = 1

    pred_log = model.predict(input_df)[0]
    fair_rent = np.expm1(pred_log)
    rent_low = fair_rent * 0.95
    rent_high = fair_rent * 1.05

    ml_data = {
        "city": city,
        "locality": locality,
        "bhk": bhk,
        "area": area,
        "furnishing": furnishing,
        "fair_rent_low": round(rent_low,0),
        "fair_rent_high": round(rent_high,0)
    }

    return jsonify(ml_data)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_question = data['user_question']
    ml_data = data['ml_data']
    chat_history = data.get('chat_history', "")

    # Call LLM
    response = get_real_estate_advice(
        bhk=ml_data['bhk'],
        locality=ml_data['locality'],
        city=ml_data['city'],
        area=ml_data['area'],
        furnishing=ml_data['furnishing'],
        predicted_rent=(ml_data['fair_rent_low'] + ml_data['fair_rent_high']) / 2,
        user_question=user_question,
        chat_history=chat_history
    )

    # Extract text from ChatCompletionMessage object
    if hasattr(response, "content"):  
        llm_response = response.content
    elif isinstance(response, list) and len(response) > 0 and hasattr(response[0], "content"):
        llm_response = response[0].content
    else:
        llm_response = str(response)

    return jsonify({"llm_response": llm_response})

if __name__ == "__main__":
    app.run(debug=True)
