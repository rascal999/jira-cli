from rich.console import Console
from rich.table import Table

console = Console()

def show_help(cli):
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")

    for command, help_text in cli.help_dict.items():
        table.add_row(f"/{command}", help_text)

    console.print(table)

def execute(cli, arg):
    show_help(cli)

COMMAND = "help"
HELP = "Show this help message."
