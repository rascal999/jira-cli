from rich.console import Console

console = Console()

def show_recent_issues(issue_manager):
    issues = issue_manager.get_recent_issues()
    if issues:
        issue_manager.display_issues_table(issues, "Recently Updated Issues")
    else:
        console.print("No recent issues found.", style="yellow")
