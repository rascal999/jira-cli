from rich.console import Console

console = Console()

def rename_ticket(issue_manager, current_ticket, new_summary):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    if issue_manager.update_issue_summary(current_ticket, new_summary):
        console.print(f"Summary updated for {current_ticket}", style="green")
        
        # Optionally, fetch and display the updated issue
        updated_issue = issue_manager.fetch_issue(current_ticket)
        if updated_issue:
            issue_manager.display_issue(updated_issue)
    else:
        console.print(f"Failed to update summary for {current_ticket}", style="red")

def execute(cli, arg):
    rename_ticket(cli.issue_manager, cli.current_ticket, arg)

COMMAND = "rename"
HELP = "Rename the summary of the currently focused ticket. Usage: /rename New summary here."
