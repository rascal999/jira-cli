import os
import json
from datetime import datetime, timedelta
from common.jira_client import get_jira_client

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'user_cache.json')

class UserCache:
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

    def get_user(self, account_id):
        if account_id in self.cache:
            cached_user = self.cache[account_id]
            cached_time = datetime.fromisoformat(cached_user['cached_time'])
            if datetime.now() - cached_time < timedelta(days=7):  # Cache for 7 days
                return cached_user
        
        return self._update_cache(account_id)

    def _update_cache(self, account_id):
        user = self.jira.user(account_id)
        user_dict = {
            'account_id': user.accountId,
            'display_name': user.displayName,
            'email_address': user.emailAddress,
            'active': user.active,
            'cached_time': datetime.now().isoformat()
        }
        
        self.cache[account_id] = user_dict
        self._save_cache()
        return user_dict

    def resolve_user_mentions(self, text, color_func):
        def replace_mention(match):
            account_id = match.group(1)
            user = self.get_user(account_id)
            display_name = user['display_name']
            color = color_func(display_name)
            return f"<<USER_MENTION:{display_name}:{color}>>"

        import re
        pattern = r'\[~accountid:([^\]]+)\]'
        return re.sub(pattern, replace_mention, text)

# Create a single instance of UserCache to be used across the application
user_cache = UserCache()

# Export the user_cache instance
__all__ = ['user_cache']
