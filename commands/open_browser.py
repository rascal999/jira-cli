import webbrowser
import os
from rich.console import Console

console = Console()

def open_in_browser(issue_manager, current_ticket, issue_key=None):
    # Use the provided issue_key if given, otherwise use the current_ticket
    ticket_to_open = issue_key or current_ticket

    if not ticket_to_open:
        console.print("No ticket specified and no ticket currently focused.", style="yellow")
        return

    try:
        issue = issue_manager.jira.issue(ticket_to_open)
        url = issue.permalink()

        # Get the browser from the environment variable, default to None (system default)
        browser = os.getenv('BROWSER')

        if browser:
            # Try to get the browser controller
            try:
                controller = webbrowser.get(browser)
                controller.open(url)
                console.print(f"Opened {ticket_to_open} in {browser}.", style="green")
            except webbrowser.Error:
                console.print(f"Specified browser '{browser}' not found. Using system default.", style="yellow")
                webbrowser.open(url)
                console.print(f"Opened {ticket_to_open} in your default browser.", style="green")
        else:
            webbrowser.open(url)
            console.print(f"Opened {ticket_to_open} in your default browser.", style="green")

    except Exception as e:
        console.print(f"Error opening {ticket_to_open} in browser: {str(e)}", style="red")
