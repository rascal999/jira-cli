from rich.console import Console

console = Console()

def view_issue(issue_manager, issue_key):
    issue = issue_manager.fetch_issue(issue_key)
    if issue:
        issue_manager.display_issue(issue)
        return issue
    else:
        console.print(f"Issue {issue_key} not found.", style="red")
        return None

def execute(cli, arg):
    if arg:
        issue = view_issue(cli.issue_manager, arg)
        if issue:
            cli.current_ticket = arg
            cli.update_prompt()
    else:
        console.print("Please provide a ticket ID. Usage: /view TICKET-ID", style="yellow")

COMMAND = "view"
HELP = "View details of a specific issue. Usage: /view TICKET-ID"
