from rich.console import Console

console = Console()

def link_issues(issue_manager, current_ticket, arg):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    if not arg:
        console.print("Please provide a ticket ID to link to.", style="yellow")
        return

    issue_manager.link_issues(current_ticket, arg)
