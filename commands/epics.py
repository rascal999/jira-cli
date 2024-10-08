from rich.console import Console

console = Console()

def list_user_epics(issue_manager):
    epics = issue_manager.get_user_epics()
    if epics:
        issue_manager.display_issues_table(epics, "User Epics")
    else:
        console.print("No epics found for the current user.", style="yellow")
