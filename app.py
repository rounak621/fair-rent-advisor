import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash, Response, stream_with_context)
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from Ai.apiCall import stream_real_estate_advice, get_real_estate_advice

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
db = mongo.cx['rent_db']          # ← the one database we work with

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

with open(os.path.join(MODELS_DIR, "locality_mapping.json"), "r") as f:
    locality_map = json.load(f)

with open(os.path.join(MODELS_DIR, "rent_model_artifacts.pkl"), "rb") as f:
    artifacts = pickle.load(f)

model              = artifacts['model']
locality_value_map = artifacts['locality_value_map']
global_mean_rent   = artifacts['global_mean_rent']
feature_columns    = artifacts['feature_columns']


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def _run_model(city, locality, bhk, area, furnishing):
    loc_val  = float(locality_value_map.get(locality, global_mean_rent))
    input_df = pd.DataFrame(0.0, index=[0], columns=feature_columns)
    input_df.at[0, 'BHK']            = bhk
    input_df.at[0, 'Area']           = area
    input_df.at[0, 'Locality_Value'] = loc_val
    if f"city_{city}" in feature_columns:
        input_df.at[0, f"city_{city}"] = 1
    if f"Furnishing_{furnishing}" in feature_columns:
        input_df.at[0, f"Furnishing_{furnishing}"] = 1
    fair_rent = np.expm1(model.predict(input_df)[0])
    return round(fair_rent * 0.95, 0), round(fair_rent * 1.05, 0)


# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template("landing.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        name     = request.form.get('name', '').strip()
        password = request.form.get('password', '')

        if not email or not name or not password:
            flash('All fields are required.', 'error')
            return render_template("signup.html")
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template("signup.html")
        if db.users.find_one({'email': email}):
            flash('An account with this email already exists.', 'error')
            return render_template("signup.html")

        result = db.users.insert_one({
            'name': name, 'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.utcnow()
        })
        session['user_id']   = str(result.inserted_id)
        session['user_name'] = name
        return redirect(url_for('dashboard'))

    return render_template("signup.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter your email and password.', 'error')
            return render_template("login.html")

        user = db.users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['user_id']   = str(user['_id'])
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.', 'error')
        return render_template("login.html")

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# ── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("index.html",
                           cities=list(locality_map.keys()),
                           cities_map=locality_map,
                           user_name=session.get('user_name'))


# ── PREDICT ───────────────────────────────────────────────────────────────────

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    d          = request.json
    city       = d.get('city', '')
    locality   = d.get('locality', '')
    bhk        = int(d.get('bhk', 2))
    area       = float(d.get('area', 1000))
    furnishing = d.get('furnishing', 'Semi-Furnished')

    low, high = _run_model(city, locality, bhk, area, furnishing)
    result = {
        "city": city, "locality": locality, "bhk": bhk,
        "area": area, "furnishing": furnishing,
        "fair_rent_low": low, "fair_rent_high": high,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        db.predictions.insert_one({
            'user_id': session['user_id'], **result,
            'created_at': datetime.utcnow(), 'note': ''
        })
    except Exception:
        pass

    return jsonify(result)


@app.route('/compare', methods=['POST'])
@login_required
def compare():
    props   = request.json.get('properties', [])
    results = []
    for p in props[:2]:
        low, high = _run_model(
            p.get('city', ''), p.get('locality', ''),
            int(p.get('bhk', 2)), float(p.get('area', 1000)),
            p.get('furnishing', 'Semi-Furnished')
        )
        results.append({**p, "fair_rent_low": low, "fair_rent_high": high,
                        "avg": (low + high) / 2})
    return jsonify(results)


# ── STREAMING CHAT ────────────────────────────────────────────────────────────

@app.route('/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    data    = request.json
    ml      = data['ml_data']
    persona = data.get('persona', 'tenant')

    def generate():
        try:
            for token in stream_real_estate_advice(
                bhk=ml['bhk'], locality=ml['locality'], city=ml['city'],
                area=ml['area'], furnishing=ml['furnishing'],
                predicted_rent=(ml['fair_rent_low'] + ml['fair_rent_high']) / 2,
                user_question=data['user_question'],
                chat_history=data.get('chat_history', ''),
                persona=persona
            ):
                yield f"data: {token.replace(chr(10), chr(92)+'n')}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {e}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ── HISTORY + NOTES ───────────────────────────────────────────────────────────

@app.route('/history', methods=['GET'])
@login_required
def history():
    try:
        records = list(
            db.predictions
            .find({'user_id': session['user_id']}, {'_id': 0})
            .sort('created_at', -1)
            .limit(20)
        )
        for r in records:
            if 'created_at' in r and hasattr(r['created_at'], 'isoformat'):
                r['created_at'] = r['created_at'].isoformat()
        return jsonify(records)
    except Exception:
        return jsonify([])


@app.route('/history/note', methods=['POST'])
@login_required
def save_note():
    d = request.json
    try:
        db.predictions.update_one(
            {'user_id': session['user_id'], 'timestamp': d.get('timestamp')},
            {'$set': {'note': d.get('note', '')}}
        )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)