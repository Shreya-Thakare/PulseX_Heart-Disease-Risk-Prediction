#!/usr/bin/env python3
"""
PulseX - Heart Risk Detection API Server
Simple HTTP server with ML prediction endpoint.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Add ml path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, 'ml')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

sys.path.insert(0, ML_DIR)

import joblib
import numpy as np
import pandas as pd

# Load models
MODEL_PATH = os.path.join(ML_DIR, 'models')
rf_model = joblib.load(os.path.join(MODEL_PATH, 'random_forest.pkl'))
lr_model = joblib.load(os.path.join(MODEL_PATH, 'logistic_regression.pkl'))
scaler = joblib.load(os.path.join(MODEL_PATH, 'scaler.pkl'))
feature_names = joblib.load(os.path.join(MODEL_PATH, 'feature_names.pkl'))

with open(os.path.join(ML_DIR, 'evaluation', 'metrics.json')) as f:
    METRICS = json.load(f)

with open(os.path.join(ML_DIR, 'evaluation', 'eda_stats.json')) as f:
    EDA_STATS = json.load(f)

FEATURE_INFO = {
    'age': {'label': 'Age', 'min': 29, 'max': 77, 'unit': 'years', 'type': 'number'},
    'sex': {'label': 'Sex', 'options': [{'value': 0, 'label': 'Female'}, {'value': 1, 'label': 'Male'}], 'type': 'select'},
    'cp': {'label': 'Chest Pain Type', 'options': [
        {'value': 0, 'label': 'Typical Angina'},
        {'value': 1, 'label': 'Atypical Angina'},
        {'value': 2, 'label': 'Non-anginal Pain'},
        {'value': 3, 'label': 'Asymptomatic'}
    ], 'type': 'select'},
    'trestbps': {'label': 'Resting Blood Pressure', 'min': 94, 'max': 200, 'unit': 'mm Hg', 'type': 'number'},
    'chol': {'label': 'Serum Cholesterol', 'min': 126, 'max': 564, 'unit': 'mg/dl', 'type': 'number'},
    'fbs': {'label': 'Fasting Blood Sugar > 120 mg/dl', 'options': [
        {'value': 0, 'label': 'No'}, {'value': 1, 'label': 'Yes'}
    ], 'type': 'select'},
    'restecg': {'label': 'Resting ECG Results', 'options': [
        {'value': 0, 'label': 'Normal'},
        {'value': 1, 'label': 'ST-T Wave Abnormality'},
        {'value': 2, 'label': 'Left Ventricular Hypertrophy'}
    ], 'type': 'select'},
    'thalach': {'label': 'Maximum Heart Rate Achieved', 'min': 71, 'max': 202, 'unit': 'bpm', 'type': 'number'},
    'exang': {'label': 'Exercise Induced Angina', 'options': [
        {'value': 0, 'label': 'No'}, {'value': 1, 'label': 'Yes'}
    ], 'type': 'select'},
    'oldpeak': {'label': 'ST Depression (induced by exercise)', 'min': 0, 'max': 6.2, 'unit': '', 'type': 'number', 'step': 0.1},
    'slope': {'label': 'Slope of Peak Exercise ST Segment', 'options': [
        {'value': 0, 'label': 'Upsloping'},
        {'value': 1, 'label': 'Flat'},
        {'value': 2, 'label': 'Downsloping'}
    ], 'type': 'select'},
    'ca': {'label': 'Number of Major Vessels (0-3) colored by fluoroscopy', 'min': 0, 'max': 4, 'unit': '', 'type': 'number'},
    'thal': {'label': 'Thalassemia', 'options': [
        {'value': 0, 'label': 'Null'},
        {'value': 1, 'label': 'Fixed Defect'},
        {'value': 2, 'label': 'Normal'},
        {'value': 3, 'label': 'Reversible Defect'}
    ], 'type': 'select'},
}


class PulseXHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/health':
            self._json_response({'status': 'ok', 'service': 'PulseX Heart Risk API'})
            return
        if path == '/api/metrics':
            self._json_response(METRICS)
            return
        if path == '/api/eda':
            self._json_response(EDA_STATS)
            return
        if path == '/api/features':
            self._json_response(FEATURE_INFO)
            return
        if path.startswith('/api/'):
            self.send_error(404, 'API endpoint not found')
            return

        # Serve static files
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/predict':
            self._handle_predict()
        else:
            self.send_error(404, 'Not found')

    def _handle_predict(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode('utf-8'))
        except Exception:
            self._json_response({'error': 'Invalid JSON'}, status=400)
            return

        try:
            # Build feature vector in correct order
            features = {}
            for name in feature_names:
                if name not in data:
                    self._json_response({'error': f'Missing feature: {name}'}, status=400)
                    return
                features[name] = float(data[name])

            X = pd.DataFrame([features], columns=feature_names)
            X_scaled = scaler.transform(X)

            # Random Forest prediction (primary)
            rf_proba = float(rf_model.predict_proba(X)[0][1])
            rf_pred = int(rf_model.predict(X)[0])

            # Logistic Regression
            lr_proba = float(lr_model.predict_proba(X_scaled)[0][1])
            lr_pred = int(lr_model.predict(X_scaled)[0])

            # Ensemble: average probability
            avg_proba = (rf_proba + lr_proba) / 2
            final_pred = 1 if avg_proba >= 0.5 else 0

            risk_level = 'Low'
            risk_color = '#5b9a8b'
            if avg_proba >= 0.75:
                risk_level = 'High'
                risk_color = '#e05c5c'
            elif avg_proba >= 0.45:
                risk_level = 'Moderate'
                risk_color = '#d4a017'

            # Feature contributions (approximate via RF)
            importances = METRICS.get('feature_importance', {})
            top_factors = sorted(importances.items(), key=lambda x: -x[1])[:5]

            response = {
                'prediction': final_pred,
                'probability': round(avg_proba * 100, 1),
                'risk_level': risk_level,
                'risk_color': risk_color,
                'message': self._get_message(final_pred, risk_level, avg_proba),
                'models': {
                    'random_forest': {'prediction': rf_pred, 'probability': round(rf_proba * 100, 1)},
                    'logistic_regression': {'prediction': lr_pred, 'probability': round(lr_proba * 100, 1)},
                },
                'top_risk_factors': [{'feature': k, 'importance': round(v * 100, 1)} for k, v in top_factors],
                'recommendations': self._get_recommendations(final_pred, data),
            }
            self._json_response(response)
        except Exception as e:
            self._json_response({'error': str(e)}, status=500)

    def _get_message(self, pred, level, proba):
        if pred == 0:
            return f"Based on the provided indicators, the estimated risk of heart disease is {level.lower()} ({proba*100:.1f}%). Continue healthy habits and regular check-ups."
        return f"The model indicates a {level.lower()} risk of heart disease ({proba*100:.1f}%). Please consult a healthcare professional for personalized advice. This is not a medical diagnosis."

    def _get_recommendations(self, pred, data):
        recs = []
        age = float(data.get('age', 50))
        chol = float(data.get('chol', 200))
        trestbps = float(data.get('trestbps', 120))
        thalach = float(data.get('thalach', 150))
        oldpeak = float(data.get('oldpeak', 0))
        exang = int(data.get('exang', 0))

        if chol > 240:
            recs.append("Cholesterol is elevated. Consider dietary changes and discuss lipid management with your doctor.")
        if trestbps > 140:
            recs.append("Resting blood pressure is high. Monitor regularly and follow lifestyle or medical advice for hypertension.")
        if thalach < 120 and age < 60:
            recs.append("Maximum heart rate appears relatively low. Discuss exercise capacity with a physician.")
        if oldpeak > 2:
            recs.append("Significant ST depression noted. This warrants clinical evaluation.")
        if exang == 1:
            recs.append("Exercise-induced angina is present. Avoid strenuous activity until cleared by a cardiologist.")
        if age > 55:
            recs.append("Age is a non-modifiable risk factor. Focus on controllable factors: diet, exercise, and stress.")
        if not recs:
            if pred == 0:
                recs.append("Maintain a balanced diet, regular physical activity, and avoid smoking.")
                recs.append("Schedule routine cardiovascular check-ups.")
            else:
                recs.append("Seek prompt medical consultation for comprehensive cardiac evaluation.")
                recs.append("Discuss medication, lifestyle modification, and further testing with your doctor.")
        return recs

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[PulseX] {args[0]}")


def main():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), PulseXHandler)
    print(f"PulseX Heart Risk Detection API running at http://localhost:{port}")
    print(f"Frontend served from: {FRONTEND_DIR}")
    print("Endpoints: /api/predict (POST), /api/metrics, /api/eda, /api/features, /api/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down PulseX server...")
        server.shutdown()


if __name__ == '__main__':
    main()
