from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

PROJECT_DIR = "/Users/shobitha/dev-analytics-platform"
VENV_PYTHON = f"{PROJECT_DIR}/venv/bin/python"
DBT_DIR = f"{PROJECT_DIR}/dbt_github_analytics"

default_args = {
    "owner": "shobitha",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="github_analytics_pipeline",
    default_args=default_args,
    description="End-to-end GitHub analytics pipeline",
    schedule="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["github", "analytics", "dbt", "mlflow"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_github_data",
        bash_command=f"cd {PROJECT_DIR}/ingestion && {VENV_PYTHON} run_ingestion.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run_models",
        bash_command=f"cd {DBT_DIR} && {PROJECT_DIR}/venv/bin/dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test_models",
        bash_command=f"cd {DBT_DIR} && {PROJECT_DIR}/venv/bin/dbt test --profiles-dir .",
    )

    ge_validate = BashOperator(
        task_id="great_expectations_validation",
        bash_command=f"cd {PROJECT_DIR}/great_expectations && {VENV_PYTHON} run_ge_validation.py",
    )

    ml_train = BashOperator(
        task_id="mlflow_train_model",
        bash_command=f"cd {PROJECT_DIR}/ml && {VENV_PYTHON} train_pr_merge_model.py",
    )

    ingest >> dbt_run >> dbt_test >> ge_validate >> ml_train
