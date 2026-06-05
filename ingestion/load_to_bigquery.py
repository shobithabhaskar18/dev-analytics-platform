import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")

client = bigquery.Client(project=PROJECT_ID)

def load_to_bq(rows, table_name):
    """Load a list of dicts into a BigQuery table, replacing it each run."""
    if not rows:
        print(f"  No rows to load for {table_name}")
        return

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    df = pd.DataFrame(rows)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

    print(f"  Loaded {len(rows)} rows into {table_id}")
