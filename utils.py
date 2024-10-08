import re
from functools import lru_cache

def resolve_user_display_name(user):
    if user:
        return user.displayName
    return "Unassigned"

def validate_issue_key(issue_key):
    pattern = r'^[A-Z]+-\d+$'
    return re.match(pattern, issue_key) is not None

@lru_cache(maxsize=128)
def cached_function(arg):
    # Implement caching for expensive operations
    pass
