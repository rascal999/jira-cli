from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return None

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Check if an epic ID is provided as an argument
        if args:
            epic_key = args[0].strip().upper()
            epic_issue = jira.issue(epic_key)
            
            # Check if the provided ticket is an epic
            if epic_issue.fields.issuetype.name.lower() == 'epic':
                # Associate the current ticket with the epic
                jira.add_issues_to_epic(epic_key, [current_ticket])
                console.print(f"[bold green]Successfully associated {current_ticket} with epic {epic_key}[/bold green]")
                return current_ticket
            else:
                console.print(f"[bold yellow]The provided ticket {epic_key} is not an epic.[/bold yellow]")
                return None

        # Existing functionality: Check if the issue has a parent
        if hasattr(issue.fields, 'parent'):
            parent_key = issue.fields.parent.key
            console.print(f"[bold green]Switching focus to parent ticket: {parent_key}[/bold green]")
            
            # Use the 'vid' module to display the parent ticket details
            from modules import vid
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

HELP_TEXT = "Switch focus to the parent ticket of the currently focused ticket or associate the current ticket with an epic (Usage: parent [EPIC-ID])"
