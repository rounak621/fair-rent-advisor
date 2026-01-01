import os
import pickle
import json
import numpy as np
import pandas as pd
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from Ai.apiCall import get_real_estate_advice

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["MONGO_URI"] =os.getenv("MONGO_URI")
mongo = PyMongo(app)

# ML Setup (Loading your artifacts)
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

# --- MIDDLEWARE (Login Required Decorator) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- AUTH ROUTES ---

@app.route('/')
def home():
    # Public Landing Page
    return render_template("landing.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users = mongo.db.users
        email = request.form.get('email')
        if users.find_one({'email': email}):
            return "User already exists!"
        
        hashed_pw = generate_password_hash(request.form.get('password'))
        users.insert_one({
            'name': request.form.get('name'),
            'email': email,
            'password': hashed_pw
        })
        return redirect(url_for('dashboard'))
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = mongo.db.users.find_one({'email': request.form.get('email')})
        if user and check_password_hash(user['password'], request.form.get('password')):
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- PROTECTED APP ROUTES ---

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("index.html", 
                        cities=list(locality_map.keys()), 
                        cities_map=locality_map,
                        user_name=session.get('user_name'))

@app.route('/predict', methods=['POST'])
@login_required
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
    
    ml_data = {
        "city": city, "locality": locality, "bhk": bhk, "area": area,
        "furnishing": furnishing,
        "fair_rent_low": round(fair_rent * 0.95, 0),
        "fair_rent_high": round(fair_rent * 1.05, 0)
    }
    return jsonify(ml_data)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    response = get_real_estate_advice(
        bhk=data['ml_data']['bhk'],
        locality=data['ml_data']['locality'],
        city=data['ml_data']['city'],
        area=data['ml_data']['area'],
        furnishing=data['ml_data']['furnishing'],
        predicted_rent=(data['ml_data']['fair_rent_low'] + data['ml_data']['fair_rent_high']) / 2,
        user_question=data['user_question'],
        chat_history=data.get('chat_history', "")
    )
    llm_response = response.content if hasattr(response, "content") else str(response)
    return jsonify({"llm_response": llm_response})

if __name__ == "__main__":
    app.run(debug=True)