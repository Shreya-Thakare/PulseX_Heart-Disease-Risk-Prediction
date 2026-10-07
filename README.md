# PulseX — Heart Risk Command Center

End-to-end system that predicts heart-disease risk from clinical features, exposes predictions through a REST API, and surfaces them in a command-center dashboard plus a dedicated Angular module.

## Project Overview

| Layer | Path | Role |
|-------|------|------|
| ML | `ml/` | Training, evaluation, model persistence |
| API | `backend/` | FastAPI or zero-dependency HTTP API on port 8000 |
| Dashboard | `frontend/` | Sidebar command center |
| Angular | `angular-module/` | Functional Angular page wired to `/predict` |
| Database | `database/schema.sql` | Patients, assessments, alerts |

## Problem Statement

Care teams need an early signal for patients who are likely higher cardiovascular risk based on standard clinical markers so follow-up can be prioritised.

## Features

- ML pipeline: Random Forest + Logistic Regression ensemble
- REST prediction API (`GET /health`, `POST /predict`)
- Command-center dashboard (Overview, Patients, Predict, Alerts, Model, Activity)
- Blue / sage clinical theme
- Patient registry with search, sort, filter, detail panel
- Risk gauge, driver breakdown, activity log
- Angular module on the same API contract
- SQL schema for patients, assessments, alerts

## Technology Stack

- Python, scikit-learn, joblib, Pandas
- FastAPI (optional) or pure Python HTTP server
- HTML / CSS / JS command center
- Angular + TypeScript + HttpClient
- MySQL-compatible SQL schema

## Architecture

```text
Angular module / Frontend dashboard
            │  POST /predict
            ▼
     Backend API  ── loads ──► ml/models/*.pkl
            │
            └── database/schema.sql
```

## API

### GET /health
Returns API + model availability.

### POST /predict
Request body includes: age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal.

Response example:
```json
{ "risk_level": "Moderate", "probability": 57.8, "high_risk_probability": 0.578, "mode": "ml" }
```

## How to Run

```bash
# 1. API
cd backend && python run_simple_api.py

# 2. Dashboard
python -m http.server 5500 --directory frontend
# open http://localhost:5500

# Optional FastAPI: python main.py
```

## Database Design

See `database/schema.sql`: `patients`, `assessments`, `alerts`.

## Model Performance

| Metric | Random Forest | Logistic Regression |
|--------|---------------|---------------------|
| Accuracy | 77.0% | 80.3% |
| ROC-AUC | 0.859 | 0.871 |

## Disclaimer

Statistical risk estimates only — not a medical device or diagnosis.

## Future Improvements

- Persist predictions to SQL
- Authentication
- SHAP explanations
- Drift monitoring

