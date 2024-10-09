from rich.console import Console

console = Console()

def list_user_epics(issue_manager):
    issue_manager.get_user_epics()