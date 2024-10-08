from rich.table import Table
from .utils import resolve_user_display_name
from rich.console import Console

console = Console()

class SearchManager:
    def __init__(self, jira_client):
        self.jira = jira_client

    def search_issues(self, jql):
        try:
            issues = self.jira.search_issues(jql)
            return issues
        except Exception as e:
            console.print(f"[red]Error during search: {e}[/red]")
            return []

    def display_search_results(self, issues):
        table = Table(title="Search Results")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Summary", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Assignee", style="yellow")

        for issue in issues:
            assignee = resolve_user_display_name(issue.fields.assignee)
            table.add_row(issue.key, issue.fields.summary, issue.fields.status.name, assignee)

        console.print(table)
