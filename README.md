# AI-Powered Developer Analytics Platform

An end-to-end data platform that ingests GitHub repository activity data via REST API, transforms it through a dbt modeling layer in BigQuery, validates data quality with Great Expectations, orchestrates workflows with Airflow, trains a PR merge probability model tracked with MLflow, and generates natural language insights via Claude API — surfaced through a live Streamlit dashboard.

**Live Dashboard:** https://dev-analytics-platform-stwxsnuyu6fkfqkbccuz44.streamlit.app

---

## Architecture

```
GitHub REST API
      │
      ▼
Python Ingestion Layer
(commits, PRs, issues, contributors)
      │
      ▼
BigQuery Raw Tables
(raw_commits · raw_pull_requests · raw_issues)
      │
      ▼
dbt Transformation Layer
(staging → marts → developer_metrics, repo_health_metrics)
      │
      ├──► Great Expectations — 22 data quality tests
      │
      ├──► MLflow — PR merge probability classifier (86.4% accuracy, 0.94 AUC)
      │
      ├──► Claude API — natural language insights for engineering leadership
      │
      └──► Streamlit Dashboard — live self-serve analytics
```

Airflow orchestrates the full pipeline on a daily schedule:
`ingest → dbt run → dbt test → great_expectations → mlflow train`

---

## Stack

| Layer | Tool |
|---|---|
| Ingestion | Python · GitHub REST API |
| Storage & Warehouse | Google BigQuery |
| Transformation | dbt |
| Data Quality | Great Expectations |
| ML Experiment Tracking | MLflow · scikit-learn |
| Orchestration | Apache Airflow |
| LLM Insights | Claude API (Anthropic) |
| Dashboard | Streamlit · Plotly |

---

## Dataset

Data pulled from 5 high-activity open source repositories:

- `tensorflow/tensorflow`
- `pytorch/pytorch`
- `kubernetes/kubernetes`
- `facebook/react`
- `microsoft/vscode`

**Volume:** 2,085 commits · 2,500 pull requests · 643 issues

---

## Engineered Metrics

| Metric | Description |
|---|---|
| PR cycle time | Time from PR open to merge (hours) |
| Code review turnaround | Avg review comments per PR per author |
| Commit frequency | Commits per contributor per week |
| Issue resolution time | Hours from issue open to close by label |
| Deploy frequency | Merges to main per week |
| Contributor merge rate | Fraction of PRs merged per author |

---

## Project Structure

```
dev-analytics-platform/
├── ingestion/
│   ├── github_client.py          # GitHub REST API client with rate limit handling
│   ├── extract_commits.py        # Commit history extractor
│   ├── extract_prs.py            # Pull request extractor with cycle time calculation
│   ├── extract_issues.py         # Issue tracker with resolution time
│   ├── load_to_bigquery.py       # BigQuery loader
│   └── run_ingestion.py          # Main ingestion runner
├── dbt_github_analytics/
│   ├── models/
│   │   ├── staging/              # Cleaned, typed views of raw tables
│   │   │   ├── stg_commits.sql
│   │   │   ├── stg_pull_requests.sql
│   │   │   ├── stg_issues.sql
│   │   │   ├── sources.yml
│   │   │   └── schema.yml        # 9 data tests including unique/not_null
│   │   └── marts/
│   │       ├── developer_metrics.sql     # Per-author productivity metrics
│   │       └── repo_health_metrics.sql   # Per-repo health summary
│   ├── dbt_project.yml
│   └── profiles.yml
├── great_expectations/
│   └── run_ge_validation.py      # 22 validation checks across 3 tables
├── ml/
│   └── train_pr_merge_model.py   # Logistic regression + MLflow tracking (3 runs)
├── airflow/
│   └── dags/
│       └── github_analytics_pipeline.py  # Daily orchestration DAG
├── llm/
│   └── generate_insights.py      # Claude API context injection + insight generation
├── dashboard/
│   └── app.py                    # Streamlit self-serve analytics dashboard
└── requirements.txt
```

---

## Key Results

- **22/22** Great Expectations data quality tests passing across all BigQuery tables
- **86.4% accuracy · 0.94 ROC-AUC** on PR merge probability classifier (3 MLflow experiment runs)
- **VSCode** identified as the highest-velocity repo at 35.5 deploys/week with 85.2% merge rate
- **Kubernetes** flagged with 483-hour average PR cycle time — longest review bottleneck across all repos
- **PyTorch** outlier detected: 1.4% merge rate vs 60%+ for other repos, surfaced automatically by Claude API insights
- dbt transformation layer produces **677 developer metric rows** and **5 repo health summaries** from raw GitHub data

---

## Resume Bullets

**1.** Architected an end-to-end AI-powered developer analytics platform in Python by building dbt transformation models on BigQuery ingesting GitHub REST API data from 5 open source repositories, orchestrating batch workflows with Airflow, and implementing 22 Great Expectations data quality checks that validated pipeline reliability across commit, PR, and issue tables.

**2.** Integrated Claude API as an LLM inference layer that generated natural language developer productivity insights from structured GitHub activity data, building a RAG-style context injection system that grounded model outputs in repository-level metrics and deployed results through a live Streamlit self-serve dashboard.

**3.** Trained a PR merge probability classifier using logistic regression on GitHub activity features, logging 3 experiment runs in MLflow tracking server with the final model achieving 86.4% accuracy and 0.94 ROC-AUC across 2,500 pull requests, and optimized BigQuery mart tables using partitioning strategies that reduced dashboard query scope.

---

## Local Setup

```bash
# Clone the repo
git clone https://github.com/shobithabhaskar18/dev-analytics-platform.git
cd dev-analytics-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in PROJECT_ID, DATASET_ID, GITHUB_TOKEN, GOOGLE_APPLICATION_CREDENTIALS, ANTHROPIC_API_KEY

# Run ingestion
cd ingestion && python run_ingestion.py

# Run dbt
cd ../dbt_github_analytics
ulimit -s unlimited && dbt run --profiles-dir .
dbt test --profiles-dir .

# Run data quality checks
cd ../great_expectations && python run_ge_validation.py

# Train ML model
cd ../ml && python train_pr_merge_model.py

# Generate LLM insights
cd ../llm && python generate_insights.py

# Launch dashboard
cd ../dashboard && streamlit run app.py
```

---

## Data Flow

1. **Ingestion** — Python scripts hit GitHub REST API (5,000 req/hr free tier) and load raw JSON-structured data into BigQuery with `WRITE_TRUNCATE` on each run
2. **Transformation** — dbt staging models clean and type raw tables into views; mart models compute developer and repo-level metrics as permanent tables
3. **Quality** — Great Expectations validates nullability, value ranges, row counts, and referential integrity before downstream consumption
4. **ML** — Features engineered from dbt marts feed a scikit-learn pipeline; MLflow logs parameters, metrics, and model artifacts across experiment runs
5. **Insights** — Claude API receives structured metric context and returns executive-ready natural language analysis grounded in real data
6. **Dashboard** — Streamlit reads directly from BigQuery marts and renders interactive Plotly charts with on-demand Claude insight generation
7. **Orchestration** — Airflow DAG chains all steps on a daily `0 6 * * *` schedule with retry logic
