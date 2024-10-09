import pyperclip
from rich.console import Console

console = Console()

def grab_url(issue_manager, current_ticket, issue_key=None):
    # Use the provided issue_key if given, otherwise use the current_ticket
    ticket_to_grab = issue_key or current_ticket

    if not ticket_to_grab:
        console.print("No ticket specified and no ticket currently focused.", style="yellow")
        return

    try:
        issue = issue_manager.jira.issue(ticket_to_grab)
        url = issue.permalink()
        pyperclip.copy(url)
        console.print(f"URL for {ticket_to_grab} copied to clipboard: {url}", style="green")
    except Exception as e:
        console.print(f"Error grabbing URL for {ticket_to_grab}: {str(e)}", style="red")

COMMAND = "grab"
HELP = "Copy URL of current or specified issue to clipboard."

def execute(cli, arg):
    grab_url(cli.issue_manager, cli.current_ticket, arg)
