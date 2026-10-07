# PulseX — Heart Risk Command Center

AI-assisted heart-disease risk estimation from standard clinical markers, with a REST API and a command-center web dashboard.

> **Disclaimer:** PulseX provides **statistical estimates only**. It is **not** a medical device and must not replace professional clinical judgment or diagnosis.

## Features

- **ML ensemble** — Random Forest + Logistic Regression (averaged probability)
- **REST API** — `GET /health`, `POST /predict` (port 8000)
- **Command center UI** — Overview, Patients, Predict, Alerts, Model, Activity
- **Risk gauge & drivers** — Clear Low / Moderate / High bands
- **Angular module** — Same `/predict` contract for a TypeScript client
- **SQL schema** — Patients, assessments, alerts

## Tech stack

| Layer | Stack |
|-------|--------|
| ML | Python, scikit-learn, pandas, joblib |
| API | Pure Python HTTP server *or* FastAPI |
| Frontend | Single-page HTML/CSS/JS dashboard |
| Optional | Angular (standalone component) |
| Data | CSV + MySQL-compatible `schema.sql` |

## Project structure

```text
final-project/
├── frontend/           # Command center (open index.html or serve statically)
├── backend/
│   ├── run_simple_api.py   # Recommended zero-dependency API
│   ├── main.py             # Optional FastAPI entrypoint
│   └── requirements.txt
├── ml/
│   ├── train_model.py
│   ├── heart.csv
│   ├── models/             # Trained .pkl artifacts
│   ├── evaluation/
│   └── visualizations/
├── database/
│   ├── schema.sql
│   └── heart_cleaned.csv
├── angular-module/         # Optional Angular predict UI
├── LICENSE
├── .gitignore
└── README.md
```

## Quick start

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/pulsex.git
cd pulsex   # or cd pulsex/final-project if the repo root is day-10
```

### 2. Install Python deps (API + ML)

```bash
pip install -r backend/requirements.txt
# or for training only:
pip install -r ml/requirements.txt
```

### 3. Start the API

```bash
cd backend
python run_simple_api.py
```

API listens on **http://localhost:8000**

- Health: `GET http://localhost:8000/health`
- Predict: `POST http://localhost:8000/predict`

### 4. Open the dashboard

```bash
# from project root
python -m http.server 5500 --directory frontend
```

Open **http://localhost:5500**

The UI works offline with a local heuristic; with the API running it uses the trained ensemble.

### Optional: FastAPI

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Optional: retrain models

```bash
cd ml
python train_model.py
```

## API example

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 54,
    "sex": 1,
    "cp": 0,
    "trestbps": 130,
    "chol": 250,
    "fbs": 0,
    "restecg": 1,
    "thalach": 150,
    "exang": 0,
    "oldpeak": 1.2,
    "slope": 1,
    "ca": 0,
    "thal": 2
  }'
```

Example response:

```json
{
  "risk_level": "Moderate",
  "probability": 57.8,
  "high_risk_probability": 0.578,
  "prediction": 1,
  "mode": "ml"
}
```

## Model performance (held-out test)

| Metric | Random Forest | Logistic Regression |
|--------|---------------|---------------------|
| Accuracy | 77.0% | **80.3%** |
| ROC-AUC | 0.859 | **0.871** |

Final risk band uses the **average** of both model probabilities.

## Database

See `database/schema.sql` for:

- `patients`
- `assessments`
- `alerts`

## License

MIT — see [LICENSE](LICENSE).

## Roadmap ideas

- Persist predictions to the database
- Auth / roles for clinical users
- Per-prediction feature explanations (e.g. SHAP)
- Drift monitoring and recalibration
