from rich.console import Console

console = Console()

def rename_ticket(issue_manager, current_ticket, new_summary):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    if issue_manager.update_issue_summary(current_ticket, new_summary):
        console.print(f"Summary updated for {current_ticket}", style="green")
    else:
        console.print(f"Failed to update summary for {current_ticket}", style="red")
