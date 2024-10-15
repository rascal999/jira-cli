import json
import os

JQL_FILTERS_FILE = 'jql_filters.json'

def save_jql_filter(name, query):
    filters = load_jql_filters()
    filters[name] = query
    save_jql_filters(filters)

def save_jql_filters(filters):
    with open(JQL_FILTERS_FILE, 'w') as f:
        json.dump(filters, f, indent=2)

def load_jql_filters():
    if os.path.exists(JQL_FILTERS_FILE):
        with open(JQL_FILTERS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Export the functions
__all__ = ['save_jql_filter', 'save_jql_filters', 'load_jql_filters']
