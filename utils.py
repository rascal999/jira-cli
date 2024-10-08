import re
from functools import lru_cache
from rich.table import Table
from rich.console import Console

console = Console()

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

def create_issue_table(issues, title):
    table = Table(title=title)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Summary", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Assignee", style="yellow")

    for issue in issues:
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        table.add_row(issue.key, issue.fields.summary, issue.fields.status.name, assignee)

    return table

def display_table(issues, title):
    table = create_issue_table(issues, title)
    console.print(table)
