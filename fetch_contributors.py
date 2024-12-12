import requests
import json
import os
import argparse
import sys
from datetime import datetime
from collections import defaultdict
import time

def check_rate_limit(headers):
    """Check GitHub API rate limit status."""
    response = requests.get('https://api.github.com/rate_limit', headers=headers)
    data = response.json()
    remaining = data['resources']['core']['remaining']
    reset_time = datetime.fromtimestamp(data['resources']['core']['reset'])
    
    if remaining < 100:
        wait_time = (reset_time - datetime.now()).total_seconds()
        if wait_time > 0:
            print(f"\nRate limit low ({remaining} remaining). Waiting {wait_time:.0f} seconds...")
            time.sleep(wait_time + 1)
    return remaining

def get_activity_summary(items, date_key="created_at"):
    """Summarize activity by year and month."""
    activity = defaultdict(lambda: defaultdict(int))
    for item in items:
        if date_key in item:
            date = datetime.strptime(item[date_key], "%Y-%m-%dT%H:%M:%SZ")
            activity[date.year][date.month] += 1
    return dict(activity)

def fetch_paginated(url, headers, is_search=False, max_pages=10):
    """Fetch paginated results from GitHub API."""
    results = []
    page = 1
    
    while page <= max_pages:
        paginated_url = f"{url}{'&' if '?' in url else '?'}page={page}&per_page=100"
        check_rate_limit(headers)
        
        try:
            response = requests.get(paginated_url, headers=headers)
            response.raise_for_status()
            
            items = response.json()
            if is_search:
                items = items.get('items', [])
            elif not isinstance(items, list):
                results.append(items)
                break
                
            if not items:
                break
                
            results.extend(items)
            if len(items) < 100:
                break
                
            page += 1
            
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching {url}: {str(e)}")
            break
            
    return results

def get_contributor_data(repo_owner, repo_name, output_dir, headers, force=False):
    """Fetch detailed contributor activity data."""
    os.makedirs(output_dir, exist_ok=True)
    
    contributors = fetch_paginated(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contributors",
        headers
    )
    
    print(f"\nProcessing {len(contributors)} contributors...")
    
    for index, contributor in enumerate(contributors, 1):
        username = contributor["login"]
        output_file = os.path.join(output_dir, f"{username}.json")
        
        if os.path.exists(output_file) and not force:
            print(f"Skipping {username} ({index}/{len(contributors)}) - existing data")
            continue
            
        print(f"\nFetching data for {username} ({index}/{len(contributors)})...")
        
        user_data = {
            "username": username,
            "avatar_url": contributor["avatar_url"],
            "total_contributions": contributor["contributions"],
            "activity": {
                "code": {},
                "issues": {},
                "engagement": {}
            }
        }

        # Fetch detailed commit data
        commits = fetch_paginated(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?author={username}",
            headers
        )
        commit_data = [{
            "sha": commit["sha"],
            "date": commit["commit"]["author"]["date"],
            "message": commit["commit"]["message"],
            "url": commit.get("html_url", ""),
        } for commit in commits]
        
        # Fetch PRs with details
        prs = fetch_paginated(
            f"https://api.github.com/search/issues?q=repo:{repo_owner}/{repo_name}+author:{username}+type:pr",
            headers,
            is_search=True
        )
        pr_data = [{
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "created_at": pr["created_at"],
            "url": pr.get("html_url", ""),
            "labels": [label["name"] for label in pr.get("labels", [])],
            "comments": pr.get("comments", 0)
        } for pr in prs]
        
        # Fetch issues with details
        issues = fetch_paginated(
            f"https://api.github.com/search/issues?q=repo:{repo_owner}/{repo_name}+author:{username}+type:issue",
            headers,
            is_search=True
        )
        issue_data = [{
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "created_at": issue["created_at"],
            "url": issue.get("html_url", ""),
            "labels": [label["name"] for label in issue.get("labels", [])],
            "comments": issue.get("comments", 0)
        } for issue in issues if "pull_request" not in issue]
        
        # Fetch detailed comments
        comments = fetch_paginated(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/comments",
            headers
        )
        comment_data = [{
            "id": comment["id"],
            "body": comment["body"],
            "created_at": comment["created_at"],
            "url": comment.get("html_url", ""),
            "type": "issue" if "/issues/" in comment.get("html_url", "") else "pr",
            "issue_number": comment["issue_url"].split("/")[-1] if comment.get("issue_url") else None
        } for comment in comments if comment["user"]["login"] == username]

        # Organize activity data
        user_data["activity"]["code"] = {
            "commits": commit_data,
            "pull_requests": pr_data,
            "total_commits": len(commit_data),
            "total_prs": len(pr_data),
            "commit_activity": get_activity_summary(commit_data, "date"),
            "pr_activity": get_activity_summary(pr_data)
        }
        
        user_data["activity"]["issues"] = {
            "opened": issue_data,
            "total_opened": len(issue_data),
            "issue_activity": get_activity_summary(issue_data)
        }
        
        user_data["activity"]["engagement"] = {
            "issue_comments": [c for c in comment_data if c["type"] == "issue"],
            "pr_comments": [c for c in comment_data if c["type"] == "pr"],
            "total_comments": len(comment_data),
            "comment_activity": get_activity_summary(comment_data)
        }

        with open(output_file, "w") as f:
            json.dump(user_data, f, indent=2)
        print(f"Saved data for {username}")

if __name__ == "__main__":
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        print("Error: Please set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="Fetch GitHub contributor activity data.")
    parser.add_argument("repo_owner", help="Repository owner")
    parser.add_argument("repo_name", help="Repository name")
    parser.add_argument("-o", "--output", default="./data/", 
                      help="Output directory")
    parser.add_argument("-f", "--force", action="store_true",
                      help="Force refresh existing data")
    
    args = parser.parse_args()
    get_contributor_data(
        args.repo_owner,
        args.repo_name,
        args.output,
        {"Authorization": f"Bearer {GITHUB_TOKEN}"},
        args.force
    )
