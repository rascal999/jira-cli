from rich.console import Console

def run(args, current_ticket=None):
    console = Console()

    if current_ticket:
        console.print(f"[bold yellow]Unfocusing current ticket: {current_ticket}[/bold yellow]")
        return "CLEARED"
    else:
        console.print("[yellow]No ticket is currently focused.[/yellow]")
        return None

HELP_TEXT = "Unfocus the current ticket"
ALIASES = ["unfocus"]

