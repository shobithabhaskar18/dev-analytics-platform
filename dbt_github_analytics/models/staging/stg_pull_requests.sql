select
    pr_number,
    repo,
    title,
    state,
    author_login,
    timestamp(created_at) as created_at,
    timestamp(merged_at) as merged_at,
    timestamp(closed_at) as closed_at,
    cycle_time_hours,
    review_comments,
    commits,
    additions,
    deletions,
    case when merged_at is not null then true else false end as is_merged
from {{ source('github_analytics', 'raw_pull_requests') }}
where pr_number is not null
