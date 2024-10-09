from rich.console import Console
from rich.table import Table
from utils import resolve_user_display_name

console = Console()

def search_issues(issue_manager, query):
    try:
        issues = issue_manager.jira.search_issues(query)
        if issues:
            display_search_results(issues)
        else:
            console.print("No issues found matching the query.", style="yellow")
    except Exception as e:
        console.print(f"Error during search: {e}", style="red")

def display_search_results(issues):
    table = Table(title="Search Results")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Summary", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Assignee", style="yellow")

    for issue in issues:
        assignee = resolve_user_display_name(issue.fields.assignee)
        table.add_row(issue.key, issue.fields.summary, issue.fields.status.name, assignee)

    console.print(table)
