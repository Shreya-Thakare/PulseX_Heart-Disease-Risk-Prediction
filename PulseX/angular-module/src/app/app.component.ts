import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface PredictResponse {
  risk_level: string;
  probability: number;
  high_risk_probability?: number;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <main style="max-width:560px;margin:2rem auto;padding:1.25rem;background:#0e1a1e;color:#e8f2f0;border-radius:14px;border:1px solid #1e383f;font-family:system-ui,sans-serif">
      <small style="color:#5b9a8b;letter-spacing:.08em;text-transform:uppercase;font-weight:700">PulseX · Angular module</small>
      <h1 style="margin:0.35rem 0 0.75rem;font-size:1.35rem">Heart Risk Predictor</h1>
      <p style="color:#8aa8a3;font-size:0.9rem">Functional Angular page connected to the PulseX <code>/predict</code> API.</p>
      <form [formGroup]="form" (ngSubmit)="submit()" style="display:grid;gap:0.55rem;margin-top:1rem">
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">Age <input type="number" formControlName="age" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">Sex (0=F,1=M) <input type="number" min="0" max="1" formControlName="sex" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">Chest pain (0–3) <input type="number" min="0" max="3" formControlName="cp" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">Resting BP <input type="number" formControlName="trestbps" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">Cholesterol <input type="number" formControlName="chol" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">Max HR <input type="number" formControlName="thalach" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">ST depression <input type="number" step="0.1" formControlName="oldpeak" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <label style="display:grid;gap:0.2rem;font-size:0.8rem;color:#8aa8a3">Vessels (ca) <input type="number" min="0" max="4" formControlName="ca" style="padding:0.5rem;border-radius:8px;border:1px solid #1e383f;background:#0b1619;color:#e8f2f0"/></label>
        <input type="hidden" formControlName="fbs"/><input type="hidden" formControlName="restecg"/>
        <input type="hidden" formControlName="exang"/><input type="hidden" formControlName="slope"/><input type="hidden" formControlName="thal"/>
        <button type="submit" [disabled]="form.invalid || loading" style="padding:0.65rem;border:0;border-radius:8px;background:linear-gradient(135deg,#2b7de9,#3d8f9a);color:#fff;font-weight:600">
          {{ loading ? 'Predicting…' : 'Predict' }}
        </button>
      </form>
      <p *ngIf="result" style="margin-top:1rem">
        Risk: <strong>{{ result.risk_level }}</strong> ({{ result.probability }}%)
      </p>
      <p *ngIf="error" style="color:#e05c5c">{{ error }}</p>
    </main>
  `,
})
export class AppComponent {
  private http = inject(HttpClient);
  private fb = inject(FormBuilder);
  loading = false;
  result: PredictResponse | null = null;
  error = '';
  form = this.fb.nonNullable.group({
    age: [54, [Validators.required]], sex: [1, [Validators.required]], cp: [0, [Validators.required]],
    trestbps: [130, [Validators.required]], chol: [240, [Validators.required]], fbs: [0], restecg: [0],
    thalach: [150, [Validators.required]], exang: [0], oldpeak: [1.0, [Validators.required]],
    slope: [1], ca: [0, [Validators.required]], thal: [2],
  });
  submit(): void {
    if (this.form.invalid) return;
    this.loading = true; this.error = ''; this.result = null;
    this.http.post<PredictResponse>('http://localhost:8000/predict', this.form.getRawValue()).subscribe({
      next: (res) => { this.result = res; this.loading = false; },
      error: () => { this.error = 'API unavailable. Start: python backend/run_simple_api.py'; this.loading = false; },
    });
  }
}
