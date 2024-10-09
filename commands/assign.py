from rich.console import Console
import time

console = Console()

def assign_issue(issue_manager, current_ticket, arg):
    ticket_to_assign = arg if arg else current_ticket
    
    if not ticket_to_assign:
        console.print("No ticket specified or currently focused. Use a ticket ID or focus on a ticket first.", style="yellow")
        return

    try:
        issue = issue_manager.jira.issue(ticket_to_assign)
        current_user = issue_manager.jira.myself()
        
        # Assign the issue using the account ID
        issue.update(assignee={'accountId': current_user['accountId']})
        
        # Wait a moment for the change to propagate
        time.sleep(1)
        
        # Refresh the issue data
        updated_issue = issue_manager.jira.issue(ticket_to_assign)
        
        console.print(f"Successfully assigned {ticket_to_assign} to {current_user['displayName']}", style="green")
        
        # Display the updated issue
        issue_manager.display_issue(updated_issue)
    except Exception as e:
        console.print(f"Error assigning issue {ticket_to_assign}: {str(e)}", style="red")

def execute(cli, arg):
    assign_issue(cli.issue_manager, cli.current_ticket, arg)

COMMAND = "assign"
HELP = "Assign the current ticket or a specified ticket to yourself."