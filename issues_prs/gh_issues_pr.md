# GitHub Issues and Pull Requests Fetcher

A powerful command-line tool to fetch and format GitHub issues and pull requests from any public or authorized repository. Provides detailed information including comments, review comments, and PR-specific data with flexible output formats.

## Features

- Fetch both issues and pull requests
- View complete comment history, including PR review comments
- Multiple output formats (pretty, JSON, CSV)
- Filter by state (open, closed, all)
- Chronologically sorted messages
- Detailed PR information (changes, mergeability, review status)
- Support for pagination (handles large repositories)
- Debug mode for troubleshooting

## Prerequisites

- Python 3.6 or higher
- GitHub CLI (`gh`) installed and authenticated
- Required Python packages: none (uses only standard library)

## Installation

1. Install the GitHub CLI:
   ```bash
   # macOS
   brew install gh

   # Windows
   winget install --id GitHub.cli

   # Ubuntu/Debian
   sudo apt install gh
   ```

2. Authenticate with GitHub:
   ```bash
   gh auth login
   ```

3. Download and make executable:
   ```bash
   chmod +x gh_issues_pr.py
   ```

## Usage

Basic syntax:
```bash
./gh_issues_pr.py <owner/repository> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-t, --type` | Item type to fetch: `issue` (default) or `pr` |
| `-f, --format` | Output format: `pretty` (default), `json`, or `csv` |
| `-s, --state` | Item state to fetch: `open` (default), `closed`, or `all` |
| `-m, --message` | Include specific message number (0 for body, 1+ for comments) |
| `-v, --verbose` | Include all messages (body and comments) |
| `--debug` | Enable debug output |

### Examples

1. View open issues (default):
   ```bash
   ./gh_issues_pr.py microsoft/vscode
   ```

2. View open pull requests:
   ```bash
   ./gh_issues_pr.py microsoft/vscode -t pr
   ```

3. Get closed PRs with their comments in JSON format:
   ```bash
   ./gh_issues_pr.py microsoft/vscode -t pr -s closed -v -f json
   ```

4. View specific comment (number 1) on an issue:
   ```bash
   ./gh_issues_pr.py microsoft/vscode -m 1
   ```

5. Export all open issues to CSV:
   ```bash
   ./gh_issues_pr.py microsoft/vscode -f csv > issues.csv
   ```

6. Debug mode for troubleshooting:
   ```bash
   ./gh_issues_pr.py microsoft/vscode --debug
   ```

## Output Formats

### Pretty Format (default)
Displays items in a human-readable format with clear sections:

```
PR #1234: Sample Pull Request Title
--------------------------------------------------------------------------------
State: open
Created: 2024-01-01 10:00:00 by username
Updated: 2024-01-02 15:30:00
Branch: feature-branch → main
Status: Ready
Mergeable: clean
Changes: +100 -50 in 10 files
Commits: 5
Comments: 3 (Reviews: 2)
URL: https://github.com/owner/repo/pull/1234

Messages:
--------------------------------------------------------------------------------
[Message #0 - body by username at 2024-01-01 10:00:00]
Original description here...

[Message #1 - comment by reviewer at 2024-01-01 11:00:00]
Regular comment here...

[Message #2 - review_comment by reviewer at 2024-01-01 12:00:00]
File: src/main.js, Line: 42, Commit: abc1234
Code review comment here...
```

### JSON Format
Outputs structured data with all fields:
```json
{
  "number": 1234,
  "title": "Sample Pull Request",
  "state": "open",
  "created_at": "2024-01-01 10:00:00",
  "updated_at": "2024-01-02 15:30:00",
  "author": "username",
  "branch": "feature-branch",
  "base_branch": "main",
  "mergeable_state": "clean",
  "draft": false,
  "comments": 3,
  "review_comments": 2,
  "messages": [
    {
      "number": 0,
      "type": "body",
      "author": "username",
      "created_at": "2024-01-01 10:00:00",
      "body": "..."
    },
    {
      "number": 1,
      "type": "review_comment",
      "author": "reviewer",
      "created_at": "2024-01-01 12:00:00",
      "body": "...",
      "path": "src/main.js",
      "line": 42,
      "commit_id": "abc1234"
    }
  ]
}
```

### CSV Format
Outputs in CSV format, ideal for spreadsheet analysis. Includes all base fields and can include messages when requested.

## Message Types

When using `-v` or `-m` flags, the tool fetches three types of messages:

1. **body** (message #0): The original issue/PR description
2. **comment**: Regular comments on the issue/PR
3. **review_comment** (PR only): Code review comments with additional context:
   - File path
   - Line number
   - Commit hash

Messages are sorted chronologically and numbered sequentially.

## Error Handling

The script includes comprehensive error handling:
- GitHub CLI installation/authentication checks
- Invalid repository format detection
- API rate limiting handling
- Network connectivity issues
- Missing field handling
- Debug mode for detailed error information

## Limitations

- Requires GitHub CLI installation and authentication
- Subject to GitHub API rate limits
- Performance may be slower for repos with many issues/PRs when using `-v`
- CSV format may not handle newlines in messages well
- Review comments are only available for PRs

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
