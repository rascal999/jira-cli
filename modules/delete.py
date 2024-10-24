import sys
from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.utils import confirm_action

def run(args, current_ticket=None):
    console = Console()

    if not args and not current_ticket:
        console.print("[bold red]Error:[/bold red] No ticket specified and no current ticket set.")
        return

    issue_keys = [arg.strip().upper() for arg in args]

    try:
        jira = get_jira_client()
        issues = []

        for issue_key in issue_keys:
            try:
                issue = jira.issue(issue_key)
                issues.append(issue)
                console.print(f"[cyan]Key:[/cyan] {issue.key} - [cyan]Summary:[/cyan] {issue.fields.summary}")
            except JIRAError as e:
                console.print(f"[bold red]Error fetching issue {issue_key}:[/bold red] {str(e)}")

        if not issues:
            console.print("[bold red]Error:[/bold red] No valid tickets to delete.")
            return

        if confirm_action("Are you sure you want to delete these issues?", default=False):
            for issue in issues:
                try:
                    issue.delete()
                    console.print(f"[bold green]Successfully deleted issue {issue.key}[/bold green]")
                except JIRAError as e:
                    console.print(f"[bold red]Error deleting issue {issue.key}:[/bold red] {str(e)}")

            # Unfocus the current ticket only if it was deleted
            if current_ticket and current_ticket in issue_keys:
                console.print(f"[bold yellow]Unfocusing current ticket: {current_ticket}[/bold yellow]")
                return "DELETED"
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Delete one or more Jira tickets (Usage: delete [TICKET-ID]...)"
ALIASES = ["rm"]
