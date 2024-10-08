from rich.console import Console

console = Console()

def list_user_epics(issue_manager):
    epics = issue_manager.get_user_epics()
    if epics:
        console.print("Your epics:", style="bold")
        for epic in epics:
            console.print(f"- {epic.key}: {epic.fields.summary}")
    else:
        console.print("You have no epics.", style="yellow")
