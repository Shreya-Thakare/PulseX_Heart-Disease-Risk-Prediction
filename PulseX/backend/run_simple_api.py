"""Zero-dependency PulseX prediction API (port 8000)."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json

PORT = 8000
ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "ml" / "models"

def rule_predict(d):
    age = float(d.get("age", 50)); chol = float(d.get("chol", 200)); bp = float(d.get("trestbps", 120))
    hr = float(d.get("thalach", 150)); oldpeak = float(d.get("oldpeak", 0)); ca = float(d.get("ca", 0))
    cp = int(d.get("cp", 0)); exang = int(d.get("exang", 0)); thal = int(d.get("thal", 2))
    score = (
        min(max((age - 40) / 40, 0), 1) * 0.1
        + min(max((chol - 180) / 200, 0), 1) * 0.1
        + min(max((bp - 110) / 80, 0), 1) * 0.1
        + min(max((170 - hr) / 100, 0), 1) * 0.12
        + min(oldpeak / 4, 1) * 0.12
        + min(ca / 3, 1) * 0.14
        + (0.85 if cp == 0 else 0.2) * 0.12
        + exang * 0.12
        + (0.8 if thal in (1, 3) else 0.25) * 0.08
    )
    prob = max(0.05, min(0.95, score))
    level = "High" if prob >= 0.75 else ("Moderate" if prob >= 0.45 else "Low")
    return {"risk_level": level, "probability": round(prob * 100, 1), "high_risk_probability": round(prob, 3),
            "prediction": 1 if prob >= 0.5 else 0, "mode": "rule-based"}

def ml_predict(d):
    try:
        import pandas as pd
        from joblib import load
    except ImportError:
        return None
    rf_path = MODEL_DIR / "random_forest.pkl"
    if not rf_path.exists():
        return None
    try:
        rf = load(rf_path)
        lr = load(MODEL_DIR / "logistic_regression.pkl")
        scaler = load(MODEL_DIR / "scaler.pkl")
        cols = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]
        row = {c: float(d.get(c, 0)) for c in cols}
        x = pd.DataFrame([row], columns=cols)
        rf_p = float(rf.predict_proba(x)[0][1])
        lr_p = float(lr.predict_proba(scaler.transform(x))[0][1])
        avg = (rf_p + lr_p) / 2
        level = "High" if avg >= 0.75 else ("Moderate" if avg >= 0.45 else "Low")
        return {"risk_level": level, "probability": round(avg * 100, 1), "high_risk_probability": round(avg, 3),
                "prediction": 1 if avg >= 0.5 else 0, "mode": "ml",
                "models": {"random_forest": {"probability": round(rf_p * 100, 1)},
                           "logistic_regression": {"probability": round(lr_p * 100, 1)}}}
    except Exception:
        return None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))
    def _send(self, code, data):
        body = json.dumps(data).encode() if data is not None else b""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if code != 204:
            self.wfile.write(body)
    def do_OPTIONS(self):
        self._send(204, None)
    def do_GET(self):
        if self.path.startswith("/health"):
            return self._send(200, {"status": "ok", "model_exists": (MODEL_DIR / "random_forest.pkl").exists(), "service": "PulseX"})
        self._send(404, {"error": "not found"})
    def do_POST(self):
        if self.path.startswith("/predict"):
            n = int(self.headers.get("Content-Length", 0))
            try:
                d = json.loads(self.rfile.read(n).decode() or "{}")
            except Exception:
                return self._send(400, {"error": "invalid json"})
            result = ml_predict(d) or rule_predict(d)
            return self._send(200, result)
        self._send(404, {"error": "not found"})

if __name__ == "__main__":
    print(f"PulseX API on http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
