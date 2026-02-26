# SmartRent AI 🏠

> ML-powered rental price prediction + Gemini AI strategist for Mumbai, Pune & Delhi rental markets.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![MongoDB](https://img.shields.io/badge/MongoDB-7.0-brightgreen) ![Docker](https://img.shields.io/badge/Docker-ready-blue)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 ML Rent Prediction | Gradient Boosted model trained on 50k+ Mumbai, Pune, Delhi listings |
| 🏙️ Hyper-local Analysis | Locality-level value mapping for accurate micro-market pricing |
| 💬 AI Strategist | Gemini Flash 2.5 powered real-estate consultant (owner & tenant modes) |
| 📊 Prediction History | All valuations saved to MongoDB per user account |
| 🔐 Auth System | Secure signup/login with bcrypt password hashing |
| 📋 Copy to Clipboard | Share results instantly |
| 📱 Responsive UI | Works on mobile, tablet, and desktop |

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

**Prerequisites:** Docker & Docker Compose installed.

```bash
# 1. Clone & enter directory
git clone <your-repo-url>
cd fair-rent-advisor

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and a strong SECRET_KEY

# 3. Start everything
docker-compose up --build

# App runs at http://localhost:5000
```

### Option 2: Local Development

**Prerequisites:** Python 3.11+, MongoDB running locally.

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in your GEMINI_API_KEY, SECRET_KEY, MONGO_URI

# 4. Run the app
python app.py
# Visits http://localhost:5000
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Flask session secret (keep private!) | `openssl rand -hex 32` |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/smartrentai` |
| `GEMINI_API_KEY` | Google Gemini API key | Get from [Google AI Studio](https://aistudio.google.com/) |

---

## 🐳 Docker Reference

```bash
# Build image
docker build -t smartrentai .

# Start with compose (includes MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop everything
docker-compose down

# Wipe data (MongoDB volume)
docker-compose down -v
```

---

## 🏗️ Project Structure

```
fair-rent-advisor/
├── app.py                    # Flask app — routes, auth, ML prediction
├── requirements.txt          # Python dependencies
├── Dockerfile                # Production Docker image
├── docker-compose.yml        # Multi-service setup (app + MongoDB)
├── .env.example              # Environment variable template
│
├── Ai/
│   └── apiCall.py            # Gemini AI strategist integration
│
├── models/
│   ├── rent_model_artifacts.pkl   # Trained ML model + encoders
│   └── locality_mapping.json      # City → locality mapping
│
├── data/
│   ├── raw/                  # Raw CSV datasets
│   └── processed/            # Cleaned data
│
├── src/
│   ├── data_pipeline.py      # Data cleaning + feature engineering
│   └── model_training.py     # Model training script
│
├── templates/
│   ├── landing.html          # Public landing page
│   ├── login.html            # Login page (with flash messages)
│   ├── signup.html           # Signup page (with flash messages)
│   └── index.html            # Main dashboard
│
└── static/
    ├── script.js             # (legacy) JS
    └── style.css             # (legacy) CSS
```

---

## 🤖 ML Model Details

- **Algorithm:** Gradient Boosting Regressor
- **Target:** Log-transformed monthly rent (₹)
- **Key Features:** BHK, Area (sqft), Locality value encoding, City one-hot, Furnishing one-hot
- **Cities:** Mumbai, Pune, Delhi
- **Prediction output:** ±5% confidence range around point estimate

### Retrain the Model

```bash
# Process raw data
python src/data_pipeline.py

# Train and save model artifacts
python src/model_training.py
```

---

## 🛣️ API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Landing page |
| `GET` | `/login` | No | Login form |
| `POST` | `/login` | No | Authenticate user |
| `GET` | `/signup` | No | Signup form |
| `POST` | `/signup` | No | Register user |
| `GET` | `/logout` | Yes | Clear session |
| `GET` | `/dashboard` | Yes | Main app |
| `POST` | `/predict` | Yes | ML rent prediction |
| `POST` | `/chat` | Yes | AI Strategist chat |
| `GET` | `/history` | Yes | Prediction history (last 10) |

---

## 📝 Changelog (v2.0 — Enhanced)

### Bug Fixes
- ✅ Fixed: Furnishing was hardcoded as "Semi-Furnished" — now user-selectable
- ✅ Fixed: Signup didn't create a session — user is now auto-logged in after signup
- ✅ Fixed: Auth errors returned raw text — replaced with styled flash messages

### New Features
- ✨ Visual furnishing selector (Unfurnished / Semi-Furnished / Furnished cards)
- ✨ BHK toggle buttons (replaces plain dropdown)
- ✨ Area slider with live display
- ✨ Prediction history tab (last 10 saved to MongoDB)
- ✨ Load any past prediction back into the dashboard
- ✨ Copy result to clipboard
- ✨ Quick-prompt chips in chat (e.g., "Is this fair?", "Negotiation tips")
- ✨ Clear chat button
- ✨ City-specific market pulse blurbs
- ✨ Price per sqft metric in results
- ✨ Toast notifications
- ✨ Dockerfile + docker-compose.yml
- ✨ Proper .env.example

---

## 📄 License

MIT — built with ❤️ for transparent Indian real estate.

---

## 📡 v3.0 — Streaming + More Features

### Streaming
- ✅ LLM responses now stream token-by-token via **Server-Sent Events (SSE)**
- ✅ Blinking cursor while AI is thinking
- ✅ Instant partial rendering — no waiting for full response

### New Features
- ✨ **Persona Mode** — Toggle between Tenant 🏠 and Owner 💼 — changes AI system prompt entirely
- ✨ **Compare Tab** — Side-by-side ML valuation of 2 different properties with auto-verdict
- ✨ **Affordability Calculator** — Enter monthly income, see rent-to-income % with green/yellow/red rating
- ✨ **Locality Typeahead** — Live search/filter on locality dropdown
- ✨ **Inline History Notes** — Add private notes to any past prediction (saved to MongoDB)
- ✨ **Full Report quick prompt** — One click for full Catalyst Report from AI
- ✨ "Hidden Costs" quick prompt added to chat panel
