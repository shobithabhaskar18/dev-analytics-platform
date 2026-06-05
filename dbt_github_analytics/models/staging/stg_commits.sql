select
    sha,
    repo,
    author_login,
    author_name,
    message,
    timestamp(committed_at) as committed_at,
    date(timestamp(committed_at)) as commit_date,
    extract(week from timestamp(committed_at)) as commit_week,
    extract(year from timestamp(committed_at)) as commit_year
from {{ source('github_analytics', 'raw_commits') }}
where sha is not null
