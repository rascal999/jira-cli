import os
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

        attachments = issue.fields.attachment

        if not attachments:
            console.print(f"[yellow]No attachments found for {current_ticket}.[/yellow]")
            return

        # Create the directory for the ticket if it doesn't exist
        ticket_dir = os.path.join("tickets", current_ticket)
        os.makedirs(ticket_dir, exist_ok=True)

        for attachment in attachments:
            file_name = attachment.filename
            file_path = os.path.join(ticket_dir, file_name)

            # Download the attachment
            with open(file_path, 'wb') as file:
                file.write(attachment.get())

            console.print(f"[bold green]Downloaded:[/bold green] {file_name}")

        console.print(f"[bold green]All attachments for {current_ticket} have been downloaded to {ticket_dir}[/bold green]")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Download all attachments for the current ticket"
ALIASES = ["download"]

