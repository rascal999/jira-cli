_last_jql_query = None

def set_last_jql(query):
    global _last_jql_query
    _last_jql_query = query

def get_last_jql():
    return _last_jql_query