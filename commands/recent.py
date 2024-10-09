from rich.console import Console

console = Console()

def execute(cli, arg):
    get_recent_issues(cli.issue_manager)

def get_recent_issues(issue_manager):
    try:
        jql = 'reporter = currentUser() ORDER BY updated DESC'
        issues = issue_manager.jira.search_issues(jql, maxResults=10)
        
        if issues:
            issue_manager.display_issues_table(issues, "Recently Updated Issues")
        else:
            console.print("No recent issues found.", style="yellow")
        
        return issues
    
    except Exception as e:
        console.print(f"Error fetching recent issues: {str(e)}", style="red")
        return []

COMMAND = "recent"
HELP = "Display recently updated issues reported by you."
