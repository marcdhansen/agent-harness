#!/usr/bin/env python3
"""
Create GitHub issues from markdown files.

Usage:
    python create_issues.py --repo marcdhansen/agent-harness --token YOUR_GITHUB_TOKEN

Or set GITHUB_TOKEN environment variable:
    export GITHUB_TOKEN=your_token_here
    python create_issues.py --repo marcdhansen/agent-harness
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    exit(1)


def parse_frontmatter(content: str) -> Dict[str, any]:
    """Extract YAML frontmatter from markdown."""
    frontmatter = {}
    
    if not content.startswith('---'):
        return frontmatter
    
    # Extract frontmatter section
    parts = content.split('---', 2)
    if len(parts) < 3:
        return frontmatter
    
    # Parse YAML-like frontmatter
    for line in parts[1].strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Handle lists
            if value.startswith('['):
                value = [v.strip() for v in value.strip('[]').split(',')]
            
            frontmatter[key] = value
    
    return frontmatter


def extract_issue_data(filepath: Path) -> Dict[str, any]:
    """Extract issue data from markdown file."""
    content = filepath.read_text()
    
    frontmatter = parse_frontmatter(content)
    
    # Remove frontmatter from body
    if content.startswith('---'):
        parts = content.split('---', 2)
        body = parts[2].strip() if len(parts) >= 3 else content
    else:
        body = content
    
    return {
        'title': frontmatter.get('title', filepath.stem),
        'body': body,
        'labels': frontmatter.get('labels', []),
        'priority': frontmatter.get('priority', 'P2'),
        'filepath': filepath
    }


def create_github_issue(repo: str, token: str, issue_data: Dict) -> Dict:
    """Create a GitHub issue via API."""
    url = f"https://api.github.com/repos/{repo}/issues"
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    payload = {
        'title': issue_data['title'],
        'body': issue_data['body'],
        'labels': issue_data['labels'] if isinstance(issue_data['labels'], list) else []
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create issue: {response.status_code} - {response.text}")


def main():
    parser = argparse.ArgumentParser(description='Create GitHub issues from markdown files')
    parser.add_argument('--repo', required=True, help='GitHub repository (owner/repo)')
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created without creating')
    parser.add_argument('--issues-dir', default='issues', help='Directory containing issue markdown files')
    
    args = parser.parse_args()
    
    # Get token from args or environment
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token and not args.dry_run:
        print("Error: GitHub token required. Set GITHUB_TOKEN env var or use --token")
        exit(1)
    
    # Find all issue markdown files
    issues_dir = Path(args.issues_dir)
    if not issues_dir.exists():
        print(f"Error: Issues directory not found: {issues_dir}")
        exit(1)
    
    issue_files = sorted(issues_dir.glob('*.md'))
    
    if not issue_files:
        print(f"No markdown files found in {issues_dir}")
        exit(1)
    
    print(f"Found {len(issue_files)} issue files")
    print()
    
    # Extract issue data
    issues = [extract_issue_data(f) for f in issue_files]
    
    # Sort by priority
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    issues.sort(key=lambda x: priority_order.get(x['priority'], 99))
    
    if args.dry_run:
        print("DRY RUN - Would create the following issues:")
        print()
        for i, issue in enumerate(issues, 1):
            print(f"{i}. [{issue['priority']}] {issue['title']}")
            print(f"   Labels: {', '.join(issue['labels']) if isinstance(issue['labels'], list) else issue['labels']}")
            print(f"   File: {issue['filepath'].name}")
            print()
    else:
        print(f"Creating issues in {args.repo}...")
        print()
        
        created = []
        failed = []
        
        for i, issue in enumerate(issues, 1):
            print(f"{i}/{len(issues)}: Creating '{issue['title']}'...", end=' ')
            
            try:
                result = create_github_issue(args.repo, token, issue)
                created.append(result)
                print(f"✓ #{result['number']}")
            except Exception as e:
                failed.append((issue, str(e)))
                print(f"✗ Failed: {e}")
        
        print()
        print("=" * 60)
        print(f"Created: {len(created)} issues")
        print(f"Failed: {len(failed)} issues")
        
        if created:
            print()
            print("Successfully created:")
            for result in created:
                print(f"  - #{result['number']}: {result['title']}")
                print(f"    {result['html_url']}")
        
        if failed:
            print()
            print("Failed to create:")
            for issue, error in failed:
                print(f"  - {issue['title']}: {error}")


if __name__ == '__main__':
    main()
