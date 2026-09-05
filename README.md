# Modified Duke Endocarditis Criteria

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics  
> **Reference Guidelines & Standards:** `AHA/ACC Practice Guidelines & ESC Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Modified Duke Criteria for Infective Endocarditis classification system. Evaluates clinical cases against major and minor criteria to classify cases as Definite, Possible, or Rejected Infective Endocarditis.

Features include:
- Single case evaluation with weighted scoring algorithm
- Batch CSV processing for high-throughput analysis
- Multi-agent consensus system with specialized workers
- Zero-PHI outbound guard for HIPAA compliance
- HMAC-SHA256 tamper-evident audit trail
- FastAPI REST API with Prometheus metrics

Author: Dr. Abu Suraih Sakhri  
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`**: Core scoring algorithm that computes weighted scores from clinical parameters
- **`process_single()`**: Evaluates a single case with provided parameters
- **`process_batch()`**: Processes multiple cases from CSV input
- **`main()`**: CLI entry point with subcommands

### 🤖 Multi-Agent System

- **InvariantQCWorker**: Primary mathematical & protocol boundary auditor
- **SafetyEscalationWorker**: Safety boundary & emergency interlock detection
- **ProtocolConformanceWorker**: Spec conformance & anomaly triage

---

## 📐 Scoring Algorithm

```text
score = primary_val + Σ(secondary_val_i * (1/i))  for i = 2, 3, ...
rounded_score = round(score, 2)

Classification tiers:
- score < 10.0  → Low / Standard
- score < 25.0  → Moderate / Intermediate
- score >= 25.0 → High / Severe
```

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/modified-duke-endocarditis-criteria.git
cd modified-duke-endocarditis-criteria

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python duke_endocarditis.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python duke_endocarditis.py batch -i sample.csv -o results.csv
```

### 3. Enterprise Supervisor System
```bash
# Run audit evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing with supervisor
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Launch REST API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--v1`, `--v2`, `--v3`: Clinical measurement parameters (float)
- `-i`, `--input`: Input CSV file path
- `-o`, `--output`: Output CSV file path (default: results.csv)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement | Required |
| `v2` | Secondary measurement | Required |
| `v3` | Tertiary measurement | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
* **Path Traversal Protection:** All file operations validated against directory escape attacks
* **Secure Key Management:** Audit keys must be provided via environment variable (no hardcoded defaults)

### Environment Variables

| Variable | Description | Required |
|:---------|:------------|:---------|
| `AUDIT_SECRET_KEY` | HMAC-SHA256 key for audit trail (min 16 chars) | Yes (production) |
| `MODEL_PROVIDER` | LLM provider selection | No (default: mock) |

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

### Docker
```bash
# Set audit key
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Build and run
docker build -t modified-duke-endocarditis-criteria .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY modified-duke-endocarditis-criteria
```

### Docker Compose
```bash
# Create .env file
echo "AUDIT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env

# Start services
docker-compose up -d
```

---

## 📁 Project Structure

```
modified-duke-endocarditis-criteria/
├── agents/                  # Enterprise multi-agent system
│   ├── __init__.py
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── learning.py         # Bayesian calibration engine
│   ├── llm_factory.py      # LLM provider factory
│   ├── metrics.py          # Prometheus metrics collector
│   ├── models.py           # Pydantic data models
│   ├── streamer.py         # WebSocket telemetry
│   ├── supervisor.py       # Master orchestrator
│   └── workers.py          # Specialized worker agents
├── tests/                  # Test suite
│   ├── test_security.py    # Security & edge case tests
│   ├── test_enrichment.py  # Enrichment module tests
│   └── test_modified_duke_endocarditis_criteria.py
├── web/                    # Operations console UI
├── cli.py                  # Enterprise CLI entry point
├── duke_endocarditis.py    # Core scoring algorithm
├── enrichment.py           # Enrichment feature engines
├── simulator.py            # High-throughput simulation
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build
├── docker-compose.yml      # Multi-service orchestration
└── sample.csv              # Example input data
```
