from rich.console import Console

console = Console()

def focus_parent_ticket(issue_manager, current_ticket):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    parent_issue = issue_manager.get_parent_issue(current_ticket)
    if parent_issue:
        issue_manager.current_ticket = parent_issue.key
        issue_manager.update_prompt()
        issue_manager.display_issue(parent_issue)
    else:
        console.print(f"No parent issue found for {current_ticket}", style="yellow")
