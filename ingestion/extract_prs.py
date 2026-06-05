from github_client import get_paginated, REPOS
from datetime import datetime

def extract_prs(repo, state="closed", max_pages=5):
    """Pull PR data including merge time for cycle time calculation."""
    owner, name = repo.split("/")

    print(f"Extracting PRs: {repo}")
    prs = get_paginated(
        f"/repos/{owner}/{name}/pulls",
        params={"state": state, "sort": "updated", "direction": "desc"},
        max_pages=max_pages
    )

    rows = []
    for pr in prs:
        created = pr.get("created_at")
        merged = pr.get("merged_at")
        closed = pr.get("closed_at")

        cycle_time_hours = None
        if created and merged:
            delta = datetime.fromisoformat(merged.replace("Z", "")) - \
                    datetime.fromisoformat(created.replace("Z", ""))
            cycle_time_hours = round(delta.total_seconds() / 3600, 2)

        rows.append({
            "repo": repo,
            "pr_number": pr.get("number"),
            "title": pr.get("title", "")[:300],
            "state": pr.get("state"),
            "author_login": pr.get("user", {}).get("login"),
            "created_at": created,
            "merged_at": merged,
            "closed_at": closed,
            "cycle_time_hours": cycle_time_hours,
            "review_comments": pr.get("review_comments", 0),
            "commits": pr.get("commits", 0),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "extracted_at": datetime.utcnow().isoformat()
        })

    print(f"  Total PRs extracted: {len(rows)}")
    return rows
