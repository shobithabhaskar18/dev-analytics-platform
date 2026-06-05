import os
import anthropic
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.expanduser("~/dev-analytics-platform/.env"))

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client_bq = bigquery.Client(project=PROJECT_ID)
client_ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def load_repo_health():
    query = f"""
        SELECT repo, total_prs, merged_prs, avg_pr_cycle_time_hours,
               avg_resolution_hours, avg_weekly_deploys, total_issues
        FROM `{PROJECT_ID}.{DATASET_ID}.repo_health_metrics`
        ORDER BY avg_pr_cycle_time_hours ASC
    """
    return client_bq.query(query).to_dataframe()

def load_top_contributors():
    query = f"""
        SELECT author_login, repo, total_prs, merged_prs,
               avg_cycle_time_hours, merge_rate, avg_review_comments
        FROM `{PROJECT_ID}.{DATASET_ID}.developer_metrics`
        WHERE total_prs >= 5
        ORDER BY merge_rate DESC
        LIMIT 10
    """
    return client_bq.query(query).to_dataframe()

def build_context(repo_df, contrib_df):
    repo_summary = repo_df.to_string(index=False)
    contrib_summary = contrib_df.to_string(index=False)

    return f"""
You are analyzing developer productivity data from 5 major open source repositories:
TensorFlow, PyTorch, Kubernetes, React, and VSCode.

REPOSITORY HEALTH METRICS:
{repo_summary}

TOP CONTRIBUTORS BY MERGE RATE:
{contrib_summary}

Columns explained:
- avg_pr_cycle_time_hours: average time from PR open to merge
- merge_rate: fraction of PRs that get merged (0 to 1)
- avg_weekly_deploys: average merges to main per week
- avg_resolution_hours: average time to close issues
"""

def generate_insights(context):
    message = client_ai.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Based on the following developer productivity metrics, 
generate a concise executive summary for engineering leadership. 
Focus on:
1. Which repositories have the healthiest development velocity
2. Key bottlenecks in PR review and merge cycles  
3. Top performing contributors and what makes them effective
4. Actionable recommendations for improving developer experience

{context}

Keep the summary to 3-4 paragraphs, using specific numbers from the data."""
            }
        ]
    )
    return message.content[0].text

if __name__ == "__main__":
    print("Loading metrics from BigQuery...")
    repo_df = load_repo_health()
    contrib_df = load_top_contributors()

    print("Building context...")
    context = build_context(repo_df, contrib_df)

    print("Generating insights with Claude API...\n")
    insights = generate_insights(context)

    print("=" * 60)
    print("DEVELOPER PRODUCTIVITY INSIGHTS")
    print("=" * 60)
    print(insights)
    print("=" * 60)

    output_path = os.path.expanduser(
        "~/dev-analytics-platform/llm/insights_output.txt"
    )
    with open(output_path, "w") as f:
        f.write(insights)
    print(f"\nInsights saved to {output_path}")
