from rich.console import Console

console = Console()

def add_comment(issue_manager, current_ticket, arg):
    if current_ticket:
        issue_manager.add_comment(current_ticket, arg)
    else:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
