from rich.console import Console
from common.jira_client import get_jira_client
from common.cache_vid import vid_cache
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a new summary for the ticket.")
        return

    new_summary = ' '.join(args)

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Update the issue summary
        issue.update(summary=new_summary)
        console.print(f"[bold green]Successfully updated summary for {current_ticket}[/bold green]")

        # Update the cache
        vid_cache._update_cache(current_ticket, issue)

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")

HELP_TEXT = "Update the summary of the current ticket (Usage: rename <NEW_SUMMARY>)"
ALIASES = ["mv"]

