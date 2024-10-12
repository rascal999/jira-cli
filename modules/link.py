from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a TICKET-ID to link to.")
        return

    target_ticket = args[0].strip().upper()

    try:
        jira = get_jira_client()
        
        # Check if both tickets exist
        current_issue = jira.issue(current_ticket)
        target_issue = jira.issue(target_ticket)

        # Create a link between the two issues
        jira.create_issue_link(
            type="Relates",
            inwardIssue=current_ticket,
            outwardIssue=target_ticket
        )

        console.print(f"[bold green]Success:[/bold green] Linked {current_ticket} to {target_ticket}")
    except JIRAError as e:
        if e.status_code == 404:
            console.print(f"[bold red]Error:[/bold red] One or both of the tickets ({current_ticket}, {target_ticket}) do not exist or you don't have permission to access them.")
        else:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")

HELP_TEXT = "Link the current ticket to another ticket (Usage: link <TICKET-ID>)"

