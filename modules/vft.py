from rich.console import Console
from modules import va, vid, vct, vli, vic
from common.utils import clear_screen  # Add this line if vft.py uses clear_screen

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    console.print(f"[bold cyan]Viewing full details for ticket: {current_ticket}[/bold cyan]\n")

    # Run vli
    console.print("[bold magenta]Linked Issues:[/bold magenta]")
    vli.run([], current_ticket)
    console.print()

    # Run va
    console.print("[bold magenta]Attachments:[/bold magenta]")
    va.run([], current_ticket)
    console.print()

    # Run vct
    console.print("[bold magenta]Child Tasks:[/bold magenta]")
    vct.run([], current_ticket)
    console.print()

    # Run vic
    console.print("[bold magenta]Comments:[/bold magenta]")
    vic.run([current_ticket])

HELP_TEXT = "View full ticket details including issue info, child tasks, linked issues, and comments"
ALIASES = ["full"]