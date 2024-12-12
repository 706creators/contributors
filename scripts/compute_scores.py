import json
import argparse

def calculate_score(contributor_data):
    """
    Calculate a weighted contribution score based on different types of GitHub activity.
    
    Weights:
    - Merged PRs: 7 points
    - Issues created/discussed: 1 point
    - Commits in merged PRs: 1 point each
    - PR reviews: 5 points
    - Comments: 0.5 points
    """
    activity = contributor_data['activity']
    
    # Calculate PR scores
    merged_prs = [pr for pr in activity['code'].get('pull_requests', []) 
                  if pr.get('state') == 'closed']
    pr_score = len(merged_prs) * 7
    
    # Calculate issue scores
    active_issues = [issue for issue in activity['issues'].get('opened', [])
                    if issue.get('comments', 0) > 0 or issue.get('state') == 'closed']
    issue_score = len(active_issues)
    
    # Calculate commit scores
    commit_score = 0
    pr_related_commits = []
    for pr in merged_prs:
        pr_commits = [commit for commit in activity['code'].get('commits', [])
                     if f"#{pr['number']}" in commit.get('message', '')]
        pr_related_commits.extend(pr_commits)
    commit_score = len(pr_related_commits)
    
    # Calculate review scores
    review_score = 0
    if 'comments' in activity['engagement']:
        pr_review_comments = [comment for comment in activity['engagement']['comments']
                            if 'review' in comment.get('body', '').lower()]
        review_score = len(pr_review_comments) * 5
    
    # Calculate comment scores (excluding review comments)
    comment_score = activity['engagement'].get('total_comments', 0) * 0.5
    
    # Compile score breakdown
    score_breakdown = {
        'merged_prs': pr_score,
        'issues': issue_score,
        'pr_commits': commit_score,
        'pr_reviews': review_score,
        'comments': comment_score,
        'total': pr_score + issue_score + commit_score + review_score + comment_score
    }
    
    return int(score_breakdown['total']), score_breakdown

def process_contributors(input_file, output_file, force=False):
    """Read contributors file, compute scores, and write updated data"""
    try:
        with open(input_file, 'r') as f:
            contributors = json.load(f)
        
        updated_contributors = []
        
        # Bot usernames to exclude
        bot_names = {'dependabot[bot]', 'github-actions[bot]', 'renovate[bot]', 'semantic-release-bot', 'imgbot[bot]', 'allcontributors[bot]'}
        
        for contributor in contributors:
            # Skip if contributor is a bot
            username = contributor['contributor']
            if username.lower() in bot_names or '[bot]' in username.lower():
                print(f"\nSkipping bot: {username}")
                continue
                
            print(f"\nProcessing {username}...")
            
            # Calculate new score
            total_score, breakdown = calculate_score(contributor)
            
            # Update contributor data
            contributor['score'] = total_score
            contributor['score_breakdown'] = breakdown
            
            print(f"Score: {total_score} ({breakdown})")
            updated_contributors.append(contributor)
        
        # Sort by score
        updated_contributors.sort(key=lambda x: x['score'], reverse=True)
        
        # Write updated data
        with open(output_file, 'w') as f:
            json.dump(updated_contributors, f, indent=2)
        
        print(f"\nSaved updated data to {output_file}")
            
    except Exception as e:
        print(f"Error processing contributors: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Compute contribution scores for GitHub users")
    parser.add_argument("input_file", help="Input contributors.json file")
    parser.add_argument("output_file", help="Output scored_contributors.json file")
    parser.add_argument("-f", "--force", action="store_true",
                       help="Force overwrite of output file if it exists")
    
    args = parser.parse_args()
    process_contributors(args.input_file, args.output_file, args.force)

if __name__ == "__main__":
    main()
