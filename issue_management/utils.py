import hashlib
import re
from datetime import datetime
from jira import JIRAError

def get_color_for_user(username):
    color_hash = hashlib.md5(username.encode()).hexdigest()
    return f"#{color_hash[:6]}"

def get_status_style(status):
    status_styles = {
        "To Do": "bold blue",
        "In Progress": "bold yellow",
        "Done": "bold green",
    }
    return status_styles.get(status, "white")

def get_available_statuses(self, issue_key):
    try:
        issue = self.fetch_issue(issue_key)
        if not issue:
            return []
        
        transitions = self.jira.transitions(issue)
        return [t['name'] for t in transitions]
    except JIRAError as e:
        self.console.print(f"Error fetching available statuses for {issue_key}: {str(e)}", style="red")
        return []

def format_date(date_string):
    date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f%z")
    return date.strftime("%Y-%m-%d %H:%M")

def resolve_user_mention(self, account_id):
    try:
        user = self.jira.user(account_id)
        display_name = user.displayName
        return (display_name, self.get_color_for_user(display_name))
    except:
        return (account_id, "white")

def fetch_issue(self, issue_key):
    if not re.match(r'^[A-Z]+-\d+$', issue_key):
        return None

    try:
        return self.jira.issue(issue_key)
    except JIRAError as e:
        if e.status_code == 404:
            return None
        else:
            self.console.print(f"Error fetching issue {issue_key}: {str(e)}", style="red")
            return None
