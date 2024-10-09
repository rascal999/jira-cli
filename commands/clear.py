from rich.console import Console

console = Console()

def clear_current_ticket(issue_manager):
    issue_manager.current_ticket = None
    issue_manager.update_prompt()
    console.print("Current ticket focus cleared.", style="green")

def clear_focus(cli):
    if cli.current_ticket:
        old_ticket = cli.current_ticket
        cli.current_ticket = None
        cli.update_prompt()
        console.print(f"Cleared focus from {old_ticket}", style="green")
    else:
        console.print("No ticket currently focused.", style="yellow")

def execute(cli, arg):
    clear_focus(cli)

COMMAND = "clear"
HELP = "Clear the current focused ticket."
