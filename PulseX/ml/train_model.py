#!/usr/bin/env python3
"""
PulseX Model Training Script
Retrains Random Forest + Logistic Regression and regenerates evaluation artifacts.
"""

import os
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score
)
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

BASE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(BASE, 'models')
EVAL = os.path.join(BASE, 'evaluation')
VIZ = os.path.join(BASE, 'visualizations')
DB = os.path.join(os.path.dirname(BASE), 'database')

os.makedirs(MODELS, exist_ok=True)
os.makedirs(EVAL, exist_ok=True)
os.makedirs(VIZ, exist_ok=True)
os.makedirs(DB, exist_ok=True)

df = pd.read_csv(os.path.join(BASE, 'heart.csv'))
df = df.drop_duplicates()
print(f"Clean records: {len(df)}")

X = df.drop('target', axis=1)
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
rf.fit(X_train, y_train)

lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_s, y_train)

def metrics(yt, yp, yprob):
    return {
        'accuracy': float(accuracy_score(yt, yp)),
        'precision': float(precision_score(yt, yp)),
        'recall': float(recall_score(yt, yp)),
        'f1': float(f1_score(yt, yp)),
        'roc_auc': float(roc_auc_score(yt, yprob)),
        'confusion_matrix': confusion_matrix(yt, yp).tolist()
    }

m_rf = metrics(y_test, rf.predict(X_test), rf.predict_proba(X_test)[:, 1])
m_lr = metrics(y_test, lr.predict(X_test_s), lr.predict_proba(X_test_s)[:, 1])
importances = dict(zip(X.columns, [float(v) for v in rf.feature_importances_]))
importances = dict(sorted(importances.items(), key=lambda x: -x[1]))

joblib.dump(rf, os.path.join(MODELS, 'random_forest.pkl'))
joblib.dump(lr, os.path.join(MODELS, 'logistic_regression.pkl'))
joblib.dump(scaler, os.path.join(MODELS, 'scaler.pkl'))
joblib.dump(list(X.columns), os.path.join(MODELS, 'feature_names.pkl'))

with open(os.path.join(EVAL, 'metrics.json'), 'w') as f:
    json.dump({'random_forest': m_rf, 'logistic_regression': m_lr, 'feature_importance': importances}, f, indent=2)

eda = {
    'total_records': int(len(df)),
    'positive_cases': int(y.sum()),
    'negative_cases': int(len(y) - y.sum()),
    'mean_age': float(df['age'].mean()),
    'mean_chol': float(df['chol'].mean()),
    'mean_thalach': float(df['thalach'].mean()),
}
with open(os.path.join(EVAL, 'eda_stats.json'), 'w') as f:
    json.dump(eda, f, indent=2)

df.to_csv(os.path.join(DB, 'heart_cleaned.csv'), index=False)

print("RF Acc:", round(m_rf['accuracy'], 3), "| LR Acc:", round(m_lr['accuracy'], 3))
print("Models saved to", MODELS)
