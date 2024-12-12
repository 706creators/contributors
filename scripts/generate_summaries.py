import json
import os
import argparse
from datetime import datetime, timedelta
from openai import OpenAI
from typing import List, Dict, Any

def get_recent_activity(data: Dict[str, Any], days: int = 7) -> List[str]:
    """Get activity from the last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    activity = []
    
    # Process commits
    if 'commits' in data['activity'].get('code', {}):
        for commit in data['activity']['code']['commits']:
            commit_date = datetime.strptime(commit['date'], "%Y-%m-%dT%H:%M:%SZ")
            if commit_date > cutoff_date:
                activity.append(f"Commit: {commit['message']}")
    
    # Process PRs
    if 'pull_requests' in data['activity'].get('code', {}):
        for pr in data['activity']['code']['pull_requests']:
            pr_date = datetime.strptime(pr['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            if pr_date > cutoff_date:
                activity.append(f"PR: {pr['title']}")
    
    # Process issues
    if 'opened' in data['activity'].get('issues', {}):
        for issue in data['activity']['issues']['opened']:
            issue_date = datetime.strptime(issue['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            if issue_date > cutoff_date:
                activity.append(f"Issue: {issue['title']}")
    
    return activity

def generate_summary(data: Dict[str, Any], api_key: str) -> str:
    """Generate a summary using OpenAI API"""
    client = OpenAI(api_key=api_key,base_url="https://api.red-pill.ai/v1") 
    
    # Get all activity for initial summary if no recent activity
    activity = get_recent_activity(data)
    if not activity:
        # If no recent activity, look at all activity
        activity = []
        if 'commits' in data['activity'].get('code', {}):
            activity.extend(f"Commit: {commit['message']}" for commit in data['activity']['code']['commits'][:10])
        if 'pull_requests' in data['activity'].get('code', {}):
            activity.extend(f"PR: {pr['title']}" for pr in data['activity']['code']['pull_requests'][:5])
        if 'opened' in data['activity'].get('issues', {}):
            activity.extend(f"Issue: {issue['title']}" for issue in data['activity']['issues']['opened'][:5])
    
    if not activity:
        return "No significant activity found in the repository."

    username = data['contributor']
    prompt = f"""Analyze the following GitHub activity for {username} and create a technical summary of their contributions:

Recent Activity:
{chr(10).join(activity)}

Repository Context:
- Total Commits: {len(data['activity'].get('code', {}).get('commits', []))}
- Total PRs: {len(data['activity'].get('code', {}).get('pull_requests', []))}
- Total Issues: {len(data['activity'].get('issues', {}).get('opened', []))}

Previous summary (if available):
{data.get('summary', 'No previous summary')}

Write a 2-3 sentence summary that:
1. Starts with "{username} is"
2. Highlights their primary areas of technical focus
3. Mentions specific projects or features they're working on
4. Notes any patterns in their contributions (e.g., focus on documentation, backend work, bug fixes)
5. Uses present tense

Keep the tone professional and focus on technical contributions."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a technical writer specializing in developer portfolio analysis. Your goal is to create clear, specific summaries that highlight a developer's technical contributions and areas of focus."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return data.get('summary', 'Unable to generate summary.')

def process_contributors(input_file: str, output_file: str, api_key: str, force: bool = False) -> None:
    """Process contributors.json file"""
    # Check if output file exists and force flag is not set
    if os.path.exists(output_file) and not force:
        raise FileExistsError(f"Output file {output_file} already exists. Use -f to overwrite.")
        
    try:
        with open(input_file, 'r') as f:
            contributors = json.load(f)
        
        updated_contributors = []
        
        for contributor in contributors:
            print(f"\nProcessing {contributor['contributor']}...")
            
            # Generate new summary
            new_summary = generate_summary(contributor, api_key)
            if new_summary:
                contributor['summary'] = new_summary
                
            print(f"Summary: {new_summary[:100]}...")
            updated_contributors.append(contributor)
        
        # Sort by score before saving
        updated_contributors.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        with open(output_file, 'w') as f:
            json.dump(updated_contributors, f, indent=2)
        
        print(f"\nSaved updated data to {output_file}")
            
    except Exception as e:
        print(f"Error processing contributors: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Generate GitHub contribution summaries")
    parser.add_argument("input_file", help="Input contributors.json file")
    parser.add_argument("output_file", help="Output contributors.json file")
    parser.add_argument("-f", "--force", action="store_true", 
                       help="Force overwrite of output file if it exists")
    args = parser.parse_args()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    process_contributors(args.input_file, args.output_file, api_key, args.force)
    print("Done!")

if __name__ == "__main__":
    main()
