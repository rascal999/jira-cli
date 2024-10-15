import sys
from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.cache_vid import vid_cache

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Get available transitions
        transitions = jira.transitions(issue)

        if not args:
            # Display available transitions
            console.print(f"[bold cyan]Available status transitions for {current_ticket}:[/bold cyan]")
            for t in transitions:
                console.print(f"- {t['name']}")
            return

        new_status = ' '.join(args).lower()

        # Find the matching transition
        transition_id = None
        for t in transitions:
            if t['name'].lower() == new_status:
                transition_id = t['id']
                break

        if transition_id:
            # Perform the transition
            jira.transition_issue(issue, transition_id)
            console.print(f"[bold green]Successfully updated status of {current_ticket} to '{new_status}'[/bold green]")
            
            # Update the cache for the current ticket
            updated_issue = jira.issue(current_ticket)
            vid_cache._update_cache(current_ticket, updated_issue)
        else:
            console.print(f"[bold red]Error:[/bold red] Invalid status '{new_status}'. Use 'status' without arguments to see available options.")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Set or view the status of the current ticket (Usage: status [NEW_STATUS])"