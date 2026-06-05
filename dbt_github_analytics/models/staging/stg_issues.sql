select
    issue_number,
    repo,
    title,
    state,
    author_login,
    labels,
    timestamp(created_at) as created_at,
    timestamp(closed_at) as closed_at,
    resolution_hours,
    comments
from {{ source('github_analytics', 'raw_issues') }}
where issue_number is not null
