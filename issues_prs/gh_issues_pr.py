#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import csv
from datetime import datetime
from typing import List, Dict, Optional, Union
import io

class GitHubFetcher:
    def __init__(self, debug=False):
        self.debug = debug
        self.verify_gh_installation()

    def log(self, message):
        """Debug logging"""
        if self.debug:
            print(f"DEBUG: {message}", file=sys.stderr)

    def verify_gh_installation(self):
        """Verify that GitHub CLI is installed and authenticated."""
        try:
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True, check=True)
            self.log(f"gh version: {result.stdout}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            sys.exit(f"Error: GitHub CLI (gh) is not installed or not in PATH.\nDetails: {str(e)}")

    def run_gh_command(self, cmd):
        """Run a gh command and handle errors"""
        self.log(f"Running command: gh {' '.join(cmd)}")
        try:
            result = subprocess.run(['gh'] + cmd, capture_output=True, text=True, check=True)
            self.log(f"Command output length: {len(result.stdout)} bytes")
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: gh {' '.join(cmd)}", file=sys.stderr)
            print(f"Error output: {e.stderr}", file=sys.stderr)
            raise

    def fetch_items(self, repo: str, state: str = 'open', message_num: Optional[int] = None, 
                   verbose: bool = False, item_type: str = 'issue') -> List[Dict]:
        """Fetch issues or pull requests from GitHub repository."""
        try:
            # Construct the API query
            if item_type == 'pr':
                # For PRs, use the search API which doesn't require base/head
                query = f'repos/{repo}/pulls?state={state}'
                params = ['api', query]
            else:
                # For issues, use the issues API
                endpoint = f'repos/{repo}/issues'
                params = ['api', endpoint, '--jq', '.[] | select(.pull_request == null)']
                if state != 'all':
                    params.extend(['--field', f'state={state}'])

            # Add pagination
            params.append('--paginate')

            # Execute API command
            self.log(f"Fetching {item_type}s with state {state} from {repo}")
            api_output = self.run_gh_command(params)
            
            # Parse JSON response
            try:
                # The output might be multiple JSON objects, one per line
                if '\n' in api_output.strip():
                    items = [json.loads(line) for line in api_output.splitlines() if line.strip()]
                    # Flatten the list if it's nested
                    if items and isinstance(items[0], list):
                        items = [item for sublist in items for item in sublist]
                else:
                    items = json.loads(api_output)
                    if not isinstance(items, list):
                        items = [items]
                
                self.log(f"Fetched {len(items)} items")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response. Raw output:", file=sys.stderr)
                print(api_output, file=sys.stderr)
                raise

            # Clean items
            cleaned_items = []
            for item in items:
                cleaned_item = self.clean_item(item, repo, message_num, verbose, item_type)
                if cleaned_item:  # Skip any None returns from clean_item
                    cleaned_items.append(cleaned_item)

            self.log(f"Processed {len(cleaned_items)} items after filtering")
            return cleaned_items

        except Exception as e:
            print(f"Error fetching items: {str(e)}", file=sys.stderr)
            raise

    def clean_item(self, item: Dict, repo: str, message_num: Optional[int] = None, 
                  verbose: bool = False, item_type: str = 'issue') -> Optional[Dict]:
        """Clean and format an issue or PR data."""
        try:
            cleaned = {
                'number': item['number'],
                'title': item['title'],
                'state': item['state'],
                'created_at': datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S'),
                'author': item['user']['login'],
                'labels': ','.join(label['name'] for label in item.get('labels', [])),
                'assignees': ','.join(assignee['login'] for assignee in item.get('assignees', [])),
                'url': item['html_url']
            }

            # Get comments count from the right field depending on type
            if item_type == 'pr':
                cleaned['comments'] = item.get('review_comments', 0) + item.get('comments', 0)
            else:
                cleaned['comments'] = item.get('comments', 0)

            if item.get('closed_at'):
                cleaned['closed_at'] = datetime.fromisoformat(item['closed_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')

            # Add PR-specific fields if it's a PR
            if item_type == 'pr':
                try:
                    cleaned.update({
                        'branch': item['head']['ref'],
                        'base_branch': item['base']['ref'],
                        'draft': item.get('draft', False),
                        'merged': item.get('merged', False),
                        'mergeable_state': item.get('mergeable_state', 'unknown'),
                        'commits': item.get('commits', 0),
                        'changed_files': item.get('changed_files', 0),
                        'additions': item.get('additions', 0),
                        'deletions': item.get('deletions', 0),
                        'review_comments': item.get('review_comments', 0),
                        'comments': item.get('comments', 0),
                        'maintainer_can_modify': item.get('maintainer_can_modify', False),
                        'rebaseable': item.get('rebaseable', False)
                    })

                    if item.get('merged_at'):
                        cleaned['merged_at'] = datetime.fromisoformat(item['merged_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                except KeyError as e:
                    self.log(f"Warning: Missing PR field {e} in item {item['number']}")

            return cleaned

        except Exception as e:
            print(f"Error cleaning item {item.get('number', 'unknown')}: {str(e)}", file=sys.stderr)
            self.log(f"Raw item data: {json.dumps(item, indent=2)}")
            return None

    def output_pretty(self, items: List[Dict], item_type: str = 'issue'):
        """Output items in a human-readable format."""
        if not items:
            print("No items found.")
            return

        for item in items:
            print(f"\n{'PR' if item_type == 'pr' else 'Issue'} #{item['number']}: {item['title']}")
            print("-" * 80)
            print(f"State: {item['state']}")
            print(f"Created: {item['created_at']} by {item['author']}")
            print(f"Updated: {item['updated_at']}")
            
            if 'closed_at' in item:
                print(f"Closed: {item['closed_at']}")
            if 'merged_at' in item:
                print(f"Merged: {item['merged_at']}")
            
            if item['assignees']:
                print(f"Assignees: {item['assignees']}")
            if item['labels']:
                print(f"Labels: {item['labels']}")
            
            if item_type == 'pr':
                print(f"Comments: {item['comments']} (Reviews: {item['review_comments']})")
            else:
                print(f"Comments: {item['comments']}")
                
            print(f"URL: {item['url']}")
            
            if item_type == 'pr':
                print(f"Branch: {item['branch']} → {item['base_branch']}")
                print(f"Status: {'Draft' if item['draft'] else 'Ready'}")
                print(f"Mergeable: {item['mergeable_state']}")
                print(f"Changes: +{item['additions']} -{item['deletions']} in {item['changed_files']} files")
                print(f"Commits: {item['commits']}")
                print(f"Maintainer can modify: {'Yes' if item['maintainer_can_modify'] else 'No'}")

    def output_json(self, items: List[Dict]):
        """Output items in JSON format."""
        if not items:
            print("[]")
            return
        print(json.dumps(items, indent=2))

    def output_csv(self, items: List[Dict]):
        """Output items in CSV format."""
        if not items:
            print("No items found.")
            return
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=items[0].keys())
        writer.writeheader()
        writer.writerows(items)
        print(output.getvalue())
        output.close()

def main():
    parser = argparse.ArgumentParser(description='Fetch GitHub issues or pull requests from a repository')
    parser.add_argument('repo', help='Repository in format owner/repo')
    parser.add_argument('-t', '--type', choices=['issue', 'pr'], 
                        default='issue', help='Type of items to fetch (default: issue)')
    parser.add_argument('-f', '--format', choices=['json', 'csv', 'pretty'], 
                        default='pretty', help='Output format (default: pretty)')
    parser.add_argument('-s', '--state', choices=['open', 'closed', 'all'],
                        default='open', help='Item state to fetch (default: open)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug output')
    
    args = parser.parse_args()

    try:
        fetcher = GitHubFetcher(debug=args.debug)
        items = fetcher.fetch_items(args.repo, args.state, item_type=args.type)

        # Output based on selected format
        if args.format == 'json':
            fetcher.output_json(items)
        elif args.format == 'csv':
            fetcher.output_csv(items)
        else:
            fetcher.output_pretty(items, args.type)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
