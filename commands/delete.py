from rich.console import Console

console = Console()

def delete_issue(issue_manager, current_ticket, issue_key):
    if not issue_key:
        if not current_ticket:
            console.print("No ticket specified and no ticket currently focused.", style="yellow")
            return
        issue_key = current_ticket

    try:
        issue = issue_manager.jira.issue(issue_key)
        issue.delete()
        console.print(f"Successfully deleted issue {issue_key}", style="green")
        
        # If the deleted issue was the current ticket, clear the focus
        if issue_key == current_ticket:
            return True  # Indicate that the current ticket was deleted
    except Exception as e:
        console.print(f"Error deleting issue {issue_key}: {str(e)}", style="red")
    
    return False