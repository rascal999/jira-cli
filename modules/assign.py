from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Get the current user
        current_user = jira.myself()

        # Try to assign using email address first, then fallback to display name
        assignment_methods = [
            ('emailAddress', lambda: jira.assign_issue(issue, current_user['emailAddress'])),
            ('displayName', lambda: jira.assign_issue(issue, current_user['displayName']))
        ]

        for identifier, method in assignment_methods:
            try:
                method()
                console.print(f"[bold green]Successfully assigned {current_ticket} to {current_user['displayName']}[/bold green]")
                return
            except JIRAError as e:
                console.print(f"[yellow]Assignment using {identifier} failed: {str(e)}[/yellow]")

        # If all methods fail, raise an exception
        raise Exception("Failed to assign the issue using available user identifiers")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Assign the current ticket to yourself"
ALIASES = ["take"]
