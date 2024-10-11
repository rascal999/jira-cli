from rich.console import Console

def delete_issue(jira, console, issue_key):
    try:
        issue = jira.issue(issue_key)
        issue.delete()
        console.print(f"Issue {issue_key} has been deleted successfully.", style="green")
        return True
    except Exception as e:
        console.print(f"Error deleting issue {issue_key}: {str(e)}", style="red")
        return False