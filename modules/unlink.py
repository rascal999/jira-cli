from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return None

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a ticket ID to unlink from.")
        return None

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)
        target_key = args[0].strip().upper()

        # Check if the target ticket exists
        try:
            target_issue = jira.issue(target_key)
        except JIRAError:
            console.print(f"[bold red]Error:[/bold red] The ticket {target_key} does not exist.")
            return None

        # Check if the current ticket is linked to the target ticket
        link_to_remove = None
        for link in issue.fields.issuelinks:
            if hasattr(link, 'outwardIssue') and link.outwardIssue.key == target_key:
                link_to_remove = link
                break
            elif hasattr(link, 'inwardIssue') and link.inwardIssue.key == target_key:
                link_to_remove = link
                break

        if not link_to_remove:
            console.print(f"[bold yellow]The current ticket {current_ticket} is not linked to {target_key}.[/bold yellow]")
            return None

        # Unlink the tickets
        jira.delete_issue_link(link_to_remove.id)
        console.print(f"[bold green]Successfully unlinked {current_ticket} from {target_key}[/bold green]")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

    return current_ticket

HELP_TEXT = "Unlink the currently focused ticket from the specified ticket (Usage: unlink TICKET-ID)"
