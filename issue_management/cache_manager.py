import os
import json
from datetime import datetime

class CacheManager:
    def __init__(self, cache_dir='.jira_cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_cache_path(self, issue_key):
        return os.path.join(self.cache_dir, f"{issue_key}.json")

    def save_issue(self, issue, get_epic_children_func=None):
        cache_data = {
            'key': issue.key,
            'fields': issue.raw['fields'],
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
