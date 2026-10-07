from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from joblib import load
from pydantic import BaseModel, Field

app = FastAPI(title="PulseX Heart Risk API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "ml" / "models"

class PatientFeatures(BaseModel):
    age: float = Field(ge=20, le=100)
    sex: int = Field(ge=0, le=1)
    cp: int = Field(ge=0, le=3)
    trestbps: float = Field(ge=80, le=250)
    chol: float = Field(ge=100, le=600)
    fbs: int = Field(ge=0, le=1)
    restecg: int = Field(ge=0, le=2)
    thalach: float = Field(ge=60, le=220)
    exang: int = Field(ge=0, le=1)
    oldpeak: float = Field(ge=0, le=10)
    slope: int = Field(ge=0, le=2)
    ca: int = Field(ge=0, le=4)
    thal: int = Field(ge=0, le=3)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_exists": (MODEL_DIR / "random_forest.pkl").exists(),
        "service": "PulseX Heart Risk API",
    }

@app.post("/predict")
def predict(data: PatientFeatures):
    rf_path = MODEL_DIR / "random_forest.pkl"
    lr_path = MODEL_DIR / "logistic_regression.pkl"
    scaler_path = MODEL_DIR / "scaler.pkl"
    if not rf_path.exists():
        raise HTTPException(503, "Train models first: run ml/train_model.py")

    rf = load(rf_path)
    lr = load(lr_path)
    scaler = load(scaler_path)
    cols = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]
    x = pd.DataFrame([data.model_dump()], columns=cols)
    rf_proba = float(rf.predict_proba(x)[0][1])
    lr_proba = float(lr.predict_proba(scaler.transform(x))[0][1])
    avg = (rf_proba + lr_proba) / 2
    level = "High" if avg >= 0.75 else ("Moderate" if avg >= 0.45 else "Low")
    return {
        "risk_level": level,
        "probability": round(avg * 100, 1),
        "high_risk_probability": round(avg, 3),
        "prediction": 1 if avg >= 0.5 else 0,
        "models": {
            "random_forest": {"probability": round(rf_proba * 100, 1)},
            "logistic_regression": {"probability": round(lr_proba * 100, 1)},
        },
        "mode": "ml",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
