from rich.console import Console

console = Console()

def focus_parent_ticket(issue_manager, current_ticket):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    try:
        issue = issue_manager.jira.issue(current_ticket)
        parent_link = next((link for link in issue.fields.issuelinks if link.type.name == "Parent"), None)
        
        if parent_link:
            parent_key = parent_link.inwardIssue.key if hasattr(parent_link, 'inwardIssue') else parent_link.outwardIssue.key
            parent_issue = issue_manager.jira.issue(parent_key)
            
            issue_manager.current_ticket = parent_issue.key
            issue_manager.update_prompt()
            issue_manager.display_issue(parent_issue)
        else:
            console.print(f"No parent issue found for {current_ticket}", style="yellow")
    except Exception as e:
        console.print(f"Error retrieving parent issue: {str(e)}", style="red")

def execute(cli, arg):
    focus_parent_ticket(cli.issue_manager, cli.current_ticket)

COMMAND = "parent"
HELP = "Change focus to parent ticket and display its details."
