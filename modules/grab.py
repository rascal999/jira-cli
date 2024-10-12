import pyperclip
from rich.console import Console
from common.jira_client import get_jira_client, JIRA_SERVER

def run(args, current_ticket=None):
    console = Console()

    if current_ticket:
        issue_key = current_ticket
    else:
        console.print("[bold red]Error:[/bold red] No current ticket set.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(issue_key)
        issue_url = f"{JIRA_SERVER}/browse/{issue.key}"
        pyperclip.copy(issue_url)
        console.print(f"[bold green]Copied issue URL for {issue.key} to clipboard.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

HELP_TEXT = "Copy the current Jira ticket URL to clipboard"

