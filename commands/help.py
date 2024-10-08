from rich.console import Console
from rich.table import Table

console = Console()

def show_help():
    console = Console()
    table = Table(title="Jira CLI Commands")

    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")

    commands = [
        ("/help", "Show this help message"),
        ("/quit", "Quit the program"),
        ("/comment <comment>", "Add a comment to the current ticket"),
        ("/recent", "Show recently updated issues"),
        ("/search <query>", "Search for issues using JQL"),
        ("/delete <issue_key>", "Delete a ticket"),
        ("/tree \[issue_key]", "Display issue tree starting from current or specified ticket"),
        ("/new", "Create a new ticket under the current ticket or a new epic"),
        ("/link <issue_key>", "Link current ticket to specified ticket or unlink if already linked"),
        ("/epics", "List all epics reported by you"),
        ("/clear", "Clear the current focused ticket"),
        ("/update", "Update the description of the current ticket"),
        ("/parent", "Change focus to parent ticket and display its details"),
        ("/ai <question>", "Ask a question to ChatGPT"),
        ("/rename <new_summary>", "Rename the summary of the currently focused ticket"),
        ("/grab \[issue_key]", "Copy URL of current or specified issue to clipboard"),
        ("/open \[issue_key]", "Open the current or specified ticket in the browser (use BROWSER env var to specify browser)"),
    ]

    for command, description in commands:
        table.add_row(command, description)

    console.print(table)

    console.print("\nNote: When viewing an issue, you can use these commands without the leading '/'.", style="yellow")
    console.print("You can also update the status of the current ticket by typing the new status.", style="yellow")
