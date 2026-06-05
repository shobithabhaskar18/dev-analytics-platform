with weekly_commits as (
    select
        repo,
        commit_year,
        commit_week,
        count(*) as weekly_commit_count,
        count(distinct author_login) as active_contributors
    from {{ ref('stg_commits') }}
    group by 1, 2, 3
),

pr_metrics as (
    select
        repo,
        count(*) as total_prs,
        countif(is_merged) as merged_prs,
        round(avg(cycle_time_hours), 2) as avg_pr_cycle_time_hours,
        countif(
            timestamp_diff(merged_at, created_at, hour) <= 24
            and is_merged
        ) as prs_merged_within_24h
    from {{ ref('stg_pull_requests') }}
    group by 1
),

issue_metrics as (
    select
        repo,
        count(*) as total_issues,
        round(avg(resolution_hours), 2) as avg_resolution_hours,
        countif(resolution_hours <= 48) as issues_resolved_within_48h
    from {{ ref('stg_issues') }}
    group by 1
),

deploy_freq as (
    select
        repo,
        count(*) as total_merges_to_main,
        round(count(*) / 12.0, 2) as avg_weekly_deploys
    from {{ ref('stg_pull_requests') }}
    where is_merged = true
    group by 1
)

select
    p.repo,
    p.total_prs,
    p.merged_prs,
    p.avg_pr_cycle_time_hours,
    p.prs_merged_within_24h,
    coalesce(i.total_issues, 0) as total_issues,
    coalesce(i.avg_resolution_hours, 0) as avg_resolution_hours,
    coalesce(i.issues_resolved_within_48h, 0) as issues_resolved_within_48h,
    coalesce(d.total_merges_to_main, 0) as total_merges_to_main,
    coalesce(d.avg_weekly_deploys, 0) as avg_weekly_deploys
from pr_metrics p
left join issue_metrics i on p.repo = i.repo
left join deploy_freq d on p.repo = d.repo
