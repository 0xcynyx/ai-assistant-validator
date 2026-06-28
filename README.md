# Waqas AI Evaluation MVP

This project is a lightweight, production-minded evaluation pipeline for reviewing AI-generated customer-support answers against policy and quality expectations. It combines deterministic rule checks with an LLM-based judge so reviewers can inspect both reproducible signals and nuanced judgment.

## What this tool does

The workflow is designed for teams that want to:

- score support replies against policy and helpfulness expectations
- keep rule-based checks in code for reproducibility
- use an LLM only for case-level judgment, not for final scoring
- generate a reviewer-friendly report and structured output artifacts

## Topology

```text
User / Reviewer
    │
    ▼
React frontend (Vite)
    │
    ▼
FastAPI backend
    │
    ├─ deterministic rule checks
    ├─ LLM judgment step
    ├─ scoring and aggregation
    └─ report generation
```

Repository layout:

```text
backend/        FastAPI API, pipeline orchestration, scoring, validation
frontend/       React UI for uploading cases and viewing reports
input/          sample case data
output/         generated artifacts such as reports and scores
policies/       policy source documents used by the evaluation flow
```

## How people use it

There are two main ways to use the system:

1. Web UI
   - Start the frontend and open the app in the browser.
   - Upload a JSON file containing cases, or use the built-in sample data.
   - Review the generated evaluation report and the scored results.

2. API
   - Send a JSON payload or file to the backend endpoint for evaluation.
   - Retrieve the generated markdown report afterwards.
   - Use the output artifacts for offline review, CI validation, or internal QA.

## Pipeline stages

The backend enforces this sequence:

```text
INIT -> CASES_LOADED -> RULE_CHECKS_COMPLETE -> LLM_EVAL_COMPLETE -> SCORES_AGGREGATED -> REPORT_GENERATED -> VALIDATION_COMPLETE -> RESULTS_FINALISED
```

Each run produces structured artifacts in the output folder, including:

- rule_checks.json
- llm_evaluations.json
- final_scores.json
- report.md
- llm_calls.jsonl
- disagreements.json (when generated)

## Evaluation approach

The pipeline uses two complementary methods:

- Deterministic checks in code for explicit and repeatable signals such as:
  - sensitive-information requests
  - absolute-guarantee or risky language
  - required-point coverage heuristics
  - response length checks
  - prompt-injection or unsafe instruction patterns

- LLM-based judgment for nuanced review such as:
  - policy adherence
  - clarity and helpfulness
  - risk level and recommended fixes

Final numeric scores are calculated in code, not by the model.

## API key requirements

A real LLM-backed evaluation run requires an API key.

### Recommended setup

Create a backend environment file and set one of the following:

```bash
cd backend
cp .env.example .env
```

Then add your key to the file:

```env
OPENROUTER_API_KEY=your_key_here
```

The backend also accepts:

```env
OPENAI_API_KEY=your_key_here
```

If no key is present, the pipeline falls back to a deterministic mock mode so you can still run the workflow end to end.

## Local setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add your OPENROUTER_API_KEY to .env
python main.py
```

You can also run the API directly with:

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will typically be available at http://localhost:3000, and the backend API at http://localhost:8000.

## Docker

If you prefer containers:

```bash
cp backend/.env.example backend/.env
# add OPENROUTER_API_KEY to backend/.env
docker compose up --build
```

Then open:

- frontend: http://localhost:3000
- backend: http://localhost:8000

## API usage

### Evaluate cases

Send a JSON array of cases, or an object with a `cases` array, to the evaluation endpoint.

```bash
curl -X POST http://localhost:8000/evaluate \
  -F "file=@/path/to/cases.json"
```

If no file is uploaded, the backend uses the default sample cases from the input folder.

### Retrieve the report

```bash
curl http://localhost:8000/report
```

### Health check

```bash
curl http://localhost:8000/health
```

## Mock mode

If the API key is missing, the system still runs the full pipeline in a clearly marked mock mode. In that mode:

- deterministic checks are still executed
- the LLM step is simulated with a structured fallback
- output artifacts are generated so the flow can be tested without a live model key

## Validation

Run the built-in validation script from the backend folder:

```bash
cd backend
python validate.py
```

This checks that the key artifacts exist and that the pipeline outputs are internally consistent.

## Notes for contributors

- Keep deterministic logic in code and avoid making the LLM the source of truth for scoring.
- Replace the sample cases file with your own evaluation set while keeping the same schema.
- The repository is intentionally scoped for an MVP and is meant to be extended with richer review workflows later.
