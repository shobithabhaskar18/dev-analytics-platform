from extract_commits import extract_commits
from extract_prs import extract_prs
from extract_issues import extract_issues
from load_to_bigquery import load_to_bq
from github_client import REPOS

def run():
    all_commits, all_prs, all_issues = [], [], []

    for repo in REPOS:
        all_commits.extend(extract_commits(repo))
        all_prs.extend(extract_prs(repo))
        all_issues.extend(extract_issues(repo))

    print("\nLoading to BigQuery...")
    load_to_bq(all_commits, "raw_commits")
    load_to_bq(all_prs, "raw_pull_requests")
    load_to_bq(all_issues, "raw_issues")
    print("\nIngestion complete.")

if __name__ == "__main__":
    run()
