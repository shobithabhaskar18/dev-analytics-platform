import os
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")

def load_data():
    client = bigquery.Client(project=PROJECT_ID)

    query = """
        select
            pr.repo,
            pr.author_login,
            pr.cycle_time_hours,
            pr.review_comments,
            pr.commits,
            pr.additions,
            pr.deletions,
            pr.is_merged,
            coalesce(dm.avg_cycle_time_hours, 0) as author_avg_cycle_time,
            coalesce(dm.merge_rate, 0) as author_merge_rate,
            coalesce(dm.avg_review_comments, 0) as author_avg_review_comments,
            coalesce(dm.total_prs, 0) as author_total_prs
        from `dev-analytics-platform-498418.github_analytics.stg_pull_requests` pr
        left join `dev-analytics-platform-498418.github_analytics.developer_metrics` dm
            on pr.repo = dm.repo
            and pr.author_login = dm.author_login
        where pr.author_login is not null
    """

    df = client.query(query).to_dataframe()
    print(f"Loaded {len(df)} rows")
    return df

def prepare_features(df):
    features = [
        'review_comments',
        'commits',
        'additions',
        'deletions',
        'author_avg_cycle_time',
        'author_merge_rate',
        'author_avg_review_comments',
        'author_total_prs'
    ]

    # Fill nulls with median
    for col in features:
        df[col] = df[col].fillna(df[col].median())

    X = df[features]
    y = df['is_merged'].astype(int)

    print(f"Features: {features}")
    print(f"Class distribution: {y.value_counts().to_dict()}")
    return X, y, features

def train(run_name, C=1.0, max_iter=200):
    df = load_data()
    X, y, features = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    mlflow.set_experiment("pr_merge_prediction")

    with mlflow.start_run(run_name=run_name):
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=C, max_iter=max_iter, random_state=42))
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]

        # Metrics
        accuracy  = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall    = recall_score(y_test, y_pred, zero_division=0)
        f1        = f1_score(y_test, y_pred, zero_division=0)
        auc       = roc_auc_score(y_test, y_prob)

        # Log to MLflow
        mlflow.log_param("C", C)
        mlflow.log_param("max_iter", max_iter)
        mlflow.log_param("features", features)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("roc_auc", auc)

        mlflow.sklearn.log_model(pipeline, "pr_merge_model")

        print(f"\nRun: {run_name}")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1:        {f1:.4f}")
        print(f"  ROC-AUC:   {auc:.4f}")

        return accuracy, auc

if __name__ == "__main__":
    print("=== Experiment 1: default ===")
    train("baseline", C=1.0, max_iter=200)

    print("\n=== Experiment 2: high regularization ===")
    train("high_regularization", C=0.1, max_iter=200)

    print("\n=== Experiment 3: low regularization ===")
    train("low_regularization", C=10.0, max_iter=500)

    print("\nAll experiments complete. Run: mlflow ui")
