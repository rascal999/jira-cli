import os
import tempfile
import subprocess
from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Create a temporary file for the comment
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.tmp', delete=False) as temp_file:
            temp_file_path = temp_file.name

        # Open the temporary file in Vim
        subprocess.call(['vim', temp_file_path])

        # Read the comment content
        with open(temp_file_path, 'r') as temp_file:
            comment_body = temp_file.read().strip()

        # Remove the temporary file
        os.unlink(temp_file_path)

        # Add the comment if it's not empty
        if comment_body:
            jira.add_comment(issue, comment_body)
            console.print(f"[bold green]Successfully added comment to {current_ticket}[/bold green]")
        else:
            console.print("[yellow]No comment was added (empty comment)[/yellow]")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")

HELP_TEXT = "Add a comment to the current ticket using Vim"

