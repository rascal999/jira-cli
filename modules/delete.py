import sys
from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.utils import confirm_action

def run(args, current_ticket=None):
    console = Console()

    if args:
        issue_key = args[0].strip().upper()
    elif current_ticket:
        issue_key = current_ticket
    else:
        console.print("[bold red]Error:[/bold red] No ticket specified and no current ticket set.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(issue_key)

        console.print(f"[yellow]You are about to delete the following issue:[/yellow]")
        console.print(f"[cyan]Key:[/cyan] {issue.key}")
        console.print(f"[cyan]Summary:[/cyan] {issue.fields.summary}")

        if confirm_action("Are you sure you want to delete this issue?"):
            issue.delete()
            console.print(f"[bold green]Successfully deleted issue {issue_key}[/bold green]")
            return "DELETED"  # Return a special value to indicate deletion
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Delete a Jira ticket (Usage: delete [TICKET-ID])"
ALIASES = ["rm"]