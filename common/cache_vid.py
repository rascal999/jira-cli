import os
import json
from datetime import datetime
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'vid_cache.json')

class VidCache:
    def __init__(self):
        self.cache = self._load_cache()
        self.jira = get_jira_client()

    def _load_cache(self):
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)

    def get_issue(self, issue_key):
        if issue_key in self.cache:
            return self.cache[issue_key]
        else:
            try:
                return self._update_cache(issue_key)
            except JIRAError as e:
                if e.status_code == 404:
                    raise ValueError(f"Issue {issue_key} does not exist or you do not have permission to see it.")
                else:
                    raise

    def _update_cache(self, issue_key, jira_issue=None):
        try:
            if not jira_issue:
                jira_issue = self.jira.issue(issue_key)
            
            # Get the description (standard or custom)
            description = self.get_description(jira_issue)
            
            issue_dict = {
                'key': jira_issue.key,
                'fields': {
                    'summary': jira_issue.fields.summary,
                    'issuetype': jira_issue.fields.issuetype.name,
                    'status': jira_issue.fields.status.name,
                    'assignee': jira_issue.fields.assignee.displayName if jira_issue.fields.assignee else 'Unassigned',
                    'reporter': jira_issue.fields.reporter.displayName,
                    'created': jira_issue.fields.created,
                    'updated': jira_issue.fields.updated,
                    'description': description
                }
            }
            
            self.cache[issue_key] = issue_dict
            self._save_cache()
            return issue_dict
        except JIRAError as e:
            if issue_key in self.cache:
                return self.cache[issue_key]
            raise

    def get_description(self, jira_issue):
        # Try to get the standard description first
        if hasattr(jira_issue.fields, 'description') and jira_issue.fields.description is not None:
            return jira_issue.fields.description

        # If standard description is not available, look for a custom field
        custom_fields = [field for field in self.jira.fields() if 'description' in field['name'].lower()]
        for field in custom_fields:
            value = getattr(jira_issue.fields, field['id'], None)
            if value:
                return value

        return 'No description available'  # Return this if no description field is found

# Create a single instance of VidCache to be used across the application
vid_cache = VidCache()

# Export the vid_cache instance
__all__ = ['vid_cache']
