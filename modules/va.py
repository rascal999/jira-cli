from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.table import create_jira_table, add_row_to_table, print_table

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

        fields_to_display = ['filename', 'size', 'created']
        table = create_jira_table(f"Attachments for {current_ticket}", fields_to_display)
        color_map = {}

        for attachment in attachments:
            attachment_obj = type('obj', (object,), {
                'key': attachment.filename,
                'fields': type('obj', (object,), {
                    'filename': attachment.filename,
                    'size': f"{attachment.size / 1024:.2f} KB",
                    'created': attachment.created
                })
            })
            add_row_to_table(table, attachment_obj, fields_to_display, color_map)

        print_table(console, table)

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "View attachments for the current ticket"
ALIASES = ["attachments"]

