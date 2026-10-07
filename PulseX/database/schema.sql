CREATE TABLE patients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  age INT NOT NULL,
  sex TINYINT NOT NULL COMMENT '0=Female,1=Male',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assessments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT NOT NULL,
  assessment_date DATE NOT NULL,
  age DECIMAL(5,2),
  sex TINYINT,
  cp TINYINT,
  trestbps DECIMAL(6,2),
  chol DECIMAL(6,2),
  fbs TINYINT,
  restecg TINYINT,
  thalach DECIMAL(6,2),
  exang TINYINT,
  oldpeak DECIMAL(5,2),
  slope TINYINT,
  ca TINYINT,
  thal TINYINT,
  risk_probability DECIMAL(6,4),
  risk_level VARCHAR(20),
  FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE TABLE alerts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(30) DEFAULT 'Open',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE INDEX idx_assessment_patient_date ON assessments(patient_id, assessment_date);
CREATE INDEX idx_alerts_status ON alerts(status);
