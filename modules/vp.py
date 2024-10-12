from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from modules import vid
from common.utils import clear_screen  # Add this line if vp.py uses clear_screen

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return None

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Check if the issue has a parent
        if hasattr(issue.fields, 'parent'):
            parent_key = issue.fields.parent.key
            console.print(f"[bold green]Parent ticket: {parent_key}[/bold green]")
            
            # Use the 'vid' module to display the parent ticket details
            vid.run([parent_key])
            
            # Return the parent key to update the current ticket
            return parent_key
        else:
            console.print(f"[bold yellow]The current ticket {current_ticket} does not have a parent.[/bold yellow]")
            return None

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

    return None

HELP_TEXT = "View the parent of the currently focused ticket"