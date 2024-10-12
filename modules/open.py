import webbrowser
from rich.console import Console
from common.jira_client import get_jira_client, JIRA_SERVER

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
        issue_url = f"{JIRA_SERVER}/browse/{issue.key}"
        webbrowser.open(issue_url)
        console.print(f"[bold green]Opened issue {issue.key} in your default browser.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

HELP_TEXT = "Open the current or specified Jira ticket in the default browser"
