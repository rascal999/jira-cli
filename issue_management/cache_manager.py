import os
import json
from datetime import datetime
import re

class CacheManager:
    def __init__(self, cache_dir='.jira_cache', jira_client=None):
        self.cache_dir = cache_dir
        self.jira_client = jira_client
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_cache_path(self, issue_key):
        return os.path.join(self.cache_dir, f"{issue_key}.json")

    def save_issue(self, issue, get_epic_children_func=None):
        cache_data = {
            'key': issue.key,
            'fields': self.resolve_account_ids(issue.raw['fields']),
            'cached_at': datetime.now().isoformat(),
            'child_tasks': []
        }

        if issue.fields.issuetype.name.lower() == 'epic' and get_epic_children_func:
            child_tasks = get_epic_children_func(issue.key)
            cache_data['child_tasks'] = [
                {
                    'key': child.key,
                    'fields': {
                        'summary': child.fields.summary
                    }
                } for child in child_tasks
            ]

        with open(self.get_cache_path(issue.key), 'w') as f:
            json.dump(cache_data, f)

    def get_issue(self, issue_key):
        cache_path = self.get_cache_path(issue_key)
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None

    def is_cache_valid(self, issue_key, updated):
        cached_issue = self.get_issue(issue_key)
        if cached_issue:
            cached_updated = cached_issue['fields'].get('updated')
            return cached_updated == updated
        return False

    def resolve_account_ids(self, fields):
        resolved_fields = {}
        for key, value in fields.items():
            if isinstance(value, dict) and 'accountId' in value:
                resolved_fields[key] = self.resolve_user(value['accountId'])
            elif isinstance(value, list):
                resolved_fields[key] = [self.resolve_account_ids(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                resolved_fields[key] = self.resolve_account_ids(value)
            else:
                resolved_fields[key] = value

        # Resolve account IDs in comments
        if 'comment' in resolved_fields:
            resolved_fields['comment']['comments'] = [
                self.resolve_comment(comment) for comment in resolved_fields['comment']['comments']
            ]

        return resolved_fields

    def resolve_user(self, account_id):
        if not account_id:
            return {'accountId': None, 'displayName': 'Unassigned', 'emailAddress': ''}
        
        try:
            user = self.jira_client.user(account_id)
            return {
                'accountId': account_id,
                'displayName': user.displayName,
                'emailAddress': user.emailAddress
            }
        except Exception as e:
            self.console.print(f"Error resolving user {account_id}: {str(e)}", style="yellow")
            return {'accountId': account_id, 'displayName': f'User {account_id}', 'emailAddress': ''}
    
    def resolve_comment(self, comment):
        resolved_comment = comment.copy()
        resolved_comment['author'] = self.resolve_user(comment['author']['accountId'])
        resolved_comment['body'] = self.resolve_mentions_in_text(comment['body'])
        return resolved_comment

    def resolve_mentions_in_text(self, text):
        mention_pattern = r'\[~accountid:([^\]]+)\]'
        
        def replace_mention(match):
            account_id = match.group(1)
            user = self.resolve_user(account_id)
            return f"@{user['displayName']}"
        
        return re.sub(mention_pattern, replace_mention, text)
