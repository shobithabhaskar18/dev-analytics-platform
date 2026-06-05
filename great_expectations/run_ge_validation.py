import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv
import great_expectations as gx

load_dotenv(dotenv_path=os.path.expanduser("~/dev-analytics-platform/.env"))

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")

client = bigquery.Client(project=PROJECT_ID)

def load_table(table_name):
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`"
    return client.query(query).to_dataframe()

def run_expectation(name, result):
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {name}")
    return result

def validate_commits(df):
    print("\n==================================================")
    print("Validation: stg_commits")
    print("==================================================")
    results = []
    results.append(run_expectation("sha not null",
        df["sha"].notna().all()))
    results.append(run_expectation("sha unique",
        df["sha"].nunique() == len(df)))
    results.append(run_expectation("repo not null",
        df["repo"].notna().all()))
    results.append(run_expectation("committed_at not null",
        df["committed_at"].notna().all()))
    results.append(run_expectation("repo in known list",
        df["repo"].isin([
            "tensorflow/tensorflow", "pytorch/pytorch",
            "kubernetes/kubernetes", "facebook/react", "microsoft/vscode"
        ]).all()))
    results.append(run_expectation("author_login 80% not null",
        df["author_login"].notna().mean() >= 0.8))
    results.append(run_expectation("row count at least 2000",
        len(df) >= 2000))
    return results

def validate_pull_requests(df):
    print("\n==================================================")
    print("Validation: stg_pull_requests")
    print("==================================================")
    results = []
    results.append(run_expectation("pr_number not null",
        df["pr_number"].notna().all()))
    results.append(run_expectation("repo not null",
        df["repo"].notna().all()))
    results.append(run_expectation("state in valid values",
        df["state"].isin(["open", "closed"]).all()))
    results.append(run_expectation("cycle_time_hours non-negative where present",
        df["cycle_time_hours"].dropna().ge(0).all()))
    results.append(run_expectation("review_comments non-negative",
        df["review_comments"].fillna(0).ge(0).all()))
    results.append(run_expectation("commits non-negative",
        df["commits"].fillna(0).ge(0).all()))
    results.append(run_expectation("row count between 2000 and 3000",
        2000 <= len(df) <= 3000))
    results.append(run_expectation("author_login 90% not null",
        df["author_login"].notna().mean() >= 0.9))
    results.append(run_expectation("merged PRs have merged_at timestamp",
        df[df["is_merged"] == True]["merged_at"].notna().all()))
    return results

def validate_issues(df):
    print("\n==================================================")
    print("Validation: stg_issues")
    print("==================================================")
    results = []
    results.append(run_expectation("issue_number not null",
        df["issue_number"].notna().all()))
    results.append(run_expectation("repo not null",
        df["repo"].notna().all()))
    results.append(run_expectation("resolution_hours non-negative where present",
        df["resolution_hours"].dropna().ge(0).all()))
    results.append(run_expectation("comments non-negative",
        df["comments"].fillna(0).ge(0).all()))
    results.append(run_expectation("row count at least 500",
        len(df) >= 500))
    results.append(run_expectation("state is closed",
        df["state"].isin(["closed"]).all()))
    return results

if __name__ == "__main__":
    print("Loading tables from BigQuery...")

    commits_df  = load_table("stg_commits")
    prs_df      = load_table("stg_pull_requests")
    issues_df   = load_table("stg_issues")

    all_results = []
    all_results.extend(validate_commits(commits_df))
    all_results.extend(validate_pull_requests(prs_df))
    all_results.extend(validate_issues(issues_df))

    passed = sum(all_results)
    failed = len(all_results) - passed

    print(f"\n==================================================")
    print(f"TOTAL: {passed} passed, {failed} failed out of {len(all_results)} tests")
    print(f"==================================================")
