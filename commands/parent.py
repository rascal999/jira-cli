from rich.console import Console

console = Console()

def focus_parent_ticket(issue_manager, current_ticket):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    try:
        issue = issue_manager.jira.issue(current_ticket)
        
        # Check for Epic link first
        if hasattr(issue.fields, 'parent'):
            parent_key = issue.fields.parent.key
        elif hasattr(issue.fields, 'customfield_10014'):  # Epic link field
            parent_key = issue.fields.customfield_10014
        else:
            # If no direct parent or epic link, check issue links
            parent_link = next((link for link in issue.fields.issuelinks 
                                if (hasattr(link, 'inwardIssue') and link.type.name in ['Parent', 'Relates']) or
                                   (hasattr(link, 'outwardIssue') and link.type.name == 'Child')), None)
            if parent_link:
                parent_key = parent_link.inwardIssue.key if hasattr(parent_link, 'inwardIssue') else parent_link.outwardIssue.key
            else:
                console.print(f"No parent issue found for {current_ticket}", style="yellow")
                return None

        parent_issue = issue_manager.jira.issue(parent_key)
        
        issue_manager.display_issue(parent_issue)
        return parent_issue.key
    except Exception as e:
        console.print(f"Error retrieving parent issue: {str(e)}", style="red")
        return None

def execute(cli, arg):
    parent_key = focus_parent_ticket(cli.issue_manager, cli.current_ticket)
    if parent_key:
        cli.current_ticket = parent_key
        cli.update_prompt()

COMMAND = "parent"
HELP = "Change focus to parent ticket and display its details."
