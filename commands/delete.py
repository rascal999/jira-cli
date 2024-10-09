from rich.console import Console
from rich.prompt import Confirm

console = Console()

def delete_issue(issue_manager, current_ticket, issue_key):
    if not issue_key:
        if not current_ticket:
            console.print("No ticket specified and no ticket currently focused.", style="yellow")
            return
        issue_key = current_ticket

    try:
        issue = issue_manager.jira.issue(issue_key)
        
        # Add confirmation prompt
        confirm = Confirm.ask(f"Are you sure you want to delete issue {issue_key}?", default=False)
        if not confirm:
            console.print("Deletion cancelled.", style="yellow")
            return False

        issue.delete()
        console.print(f"Successfully deleted issue {issue_key}", style="green")
        
        # If the deleted issue was the current ticket, clear the focus
        if issue_key == current_ticket:
            return True  # Indicate that the current ticket was deleted
    except Exception as e:
        console.print(f"Error deleting issue {issue_key}: {str(e)}", style="red")
    
    return False

def execute(cli, arg):
    if delete_issue(cli.issue_manager, cli.current_ticket, arg):
        cli.current_ticket = None
        cli.update_prompt()
        console.print("Unfocused deleted ticket.", style="green")

COMMAND = "delete"
HELP = "Delete a ticket. Usage: /delete [TICKET_ID]"
