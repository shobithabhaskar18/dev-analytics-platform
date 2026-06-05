with commits as (
    select
        repo,
        author_login,
        commit_week,
        commit_year,
        count(*) as weekly_commits
    from {{ ref('stg_commits') }}
    where author_login is not null
    group by 1, 2, 3, 4
),

prs as (
    select
        repo,
        author_login,
        count(*) as total_prs,
        countif(is_merged) as merged_prs,
        round(avg(cycle_time_hours), 2) as avg_cycle_time_hours,
        round(avg(review_comments), 2) as avg_review_comments,
        safe_divide(countif(is_merged), count(*)) as merge_rate
    from {{ ref('stg_pull_requests') }}
    where author_login is not null
    group by 1, 2
),

issues as (
    select
        repo,
        author_login,
        count(*) as total_issues_opened,
        round(avg(resolution_hours), 2) as avg_issue_resolution_hours
    from {{ ref('stg_issues') }}
    where author_login is not null
    group by 1, 2
)

select
    p.repo,
    p.author_login,
    p.total_prs,
    p.merged_prs,
    p.avg_cycle_time_hours,
    p.avg_review_comments,
    p.merge_rate,
    coalesce(i.total_issues_opened, 0) as total_issues_opened,
    coalesce(i.avg_issue_resolution_hours, 0) as avg_issue_resolution_hours
from prs p
left join issues i
    on p.repo = i.repo
    and p.author_login = i.author_login
