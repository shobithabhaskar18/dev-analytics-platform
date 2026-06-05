import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account
import anthropic

PROJECT_ID = "dev-analytics-platform-498418"
DATASET_ID = "github_analytics"

@st.cache_resource
def get_bq_client():
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)
    else:
        return bigquery.Client(project=PROJECT_ID)

@st.cache_resource
def get_ai_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
    return anthropic.Anthropic(api_key=api_key)

@st.cache_data(ttl=3600)
def load_repo_health():
    client = get_bq_client()
    query = f"""
        SELECT repo, total_prs, merged_prs, avg_pr_cycle_time_hours,
               avg_resolution_hours, avg_weekly_deploys, total_issues
        FROM `{PROJECT_ID}.{DATASET_ID}.repo_health_metrics`
        ORDER BY avg_weekly_deploys DESC
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=3600)
def load_developer_metrics():
    client = get_bq_client()
    query = f"""
        SELECT author_login, repo, total_prs, merged_prs,
               avg_cycle_time_hours, merge_rate, avg_review_comments
        FROM `{PROJECT_ID}.{DATASET_ID}.developer_metrics`
        WHERE total_prs >= 5
        ORDER BY merge_rate DESC
        LIMIT 20
    """
    return client.query(query).to_dataframe()

def generate_insights(repo_df, contrib_df):
    client = get_ai_client()
    context = f"""
Repository health metrics:
{repo_df.to_string(index=False)}

Top contributors:
{contrib_df.head(10).to_string(index=False)}
"""
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"Based on this developer productivity data, write a 2-paragraph executive summary highlighting the most important findings and one key recommendation. Use specific numbers. Be direct and concise.\n\n{context}"
        }]
    )
    return message.content[0].text

st.set_page_config(page_title="Developer Analytics Platform", page_icon="📊", layout="wide")
st.title("📊 Developer Analytics Platform")
st.caption("AI-powered insights from GitHub activity data across 5 major open source repositories")

with st.spinner("Loading metrics from BigQuery..."):
    repo_df = load_repo_health()
    dev_df = load_developer_metrics()

st.subheader("Repository Health Overview")
cols = st.columns(5)
for i, row in repo_df.iterrows():
    repo_short = row["repo"].split("/")[1]
    cols[i % 5].metric(
        label=repo_short,
        value=f"{row['avg_weekly_deploys']:.1f} deploys/wk",
        delta=f"{row['merged_prs']} PRs merged"
    )

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("PR Cycle Time by Repository")
    fig = px.bar(
        repo_df.sort_values("avg_pr_cycle_time_hours"),
        x="avg_pr_cycle_time_hours",
        y="repo",
        orientation="h",
        color="avg_pr_cycle_time_hours",
        color_continuous_scale="RdYlGn_r",
        labels={"avg_pr_cycle_time_hours": "Avg Hours", "repo": "Repository"},
    )
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Merge Rate vs Deploy Frequency")
    repo_df["merge_rate"] = repo_df["merged_prs"] / repo_df["total_prs"]
    fig2 = px.scatter(
        repo_df,
        x="avg_weekly_deploys",
        y="merge_rate",
        size="total_prs",
        text="repo",
        labels={"avg_weekly_deploys": "Weekly Deploys", "merge_rate": "Merge Rate"},
        color="merge_rate",
        color_continuous_scale="Viridis"
    )
    fig2.update_traces(textposition="top center")
    fig2.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("Top Contributors by Merge Rate")
    display_df = dev_df[["author_login", "repo", "total_prs", "merge_rate", "avg_cycle_time_hours"]].copy()
    display_df["merge_rate"] = (display_df["merge_rate"] * 100).round(1)
    display_df["avg_cycle_time_hours"] = display_df["avg_cycle_time_hours"].round(1)
    display_df.columns = ["Contributor", "Repo", "Total PRs", "Merge Rate %", "Avg Cycle Time (hrs)"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with col4:
    st.subheader("Issue Resolution Time by Repository")
    fig3 = px.bar(
        repo_df.sort_values("avg_resolution_hours", ascending=False),
        x="repo",
        y="avg_resolution_hours",
        color="avg_resolution_hours",
        color_continuous_scale="Reds",
        labels={"avg_resolution_hours": "Avg Hours", "repo": "Repository"}
    )
    fig3.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

st.subheader("🤖 AI-Generated Executive Insights")
st.caption("Powered by Claude API — grounded in live BigQuery metrics")

if st.button("Generate Insights", type="primary"):
    with st.spinner("Analyzing metrics with Claude..."):
        insights = generate_insights(repo_df, dev_df)
    st.success("Analysis complete")
    st.markdown(insights)
else:
    insights_path = os.path.expanduser("~/dev-analytics-platform/llm/insights_output.txt")
    if os.path.exists(insights_path):
        with open(insights_path) as f:
            cached = f.read()
        st.info("Showing cached insights. Click Generate Insights to refresh.")
        st.markdown(cached)
