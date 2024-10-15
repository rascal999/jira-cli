from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.table import create_jira_table, add_row_to_table, print_table

def run(args, current_ticket=None):
    console = Console()

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a PROJECT ID.")
        return []

    project_id = args[0].upper()

    try:
        jira = get_jira_client()
        
        # Get project
        project = jira.project(project_id)
        
        # Get all users in the project
        users = jira.search_assignable_users_for_projects('', project_id)

        if not users:
            console.print(f"[yellow]No team members found for project {project_id}.[/yellow]")
            return []

        fields_to_display = ['emailAddress', 'displayName', 'active']
        table = create_jira_table(f"Team Members for {project.name} ({project_id})", fields_to_display)
        color_map = {}

        for user in users:
            user_obj = type('obj', (object,), {
                'key': user.accountId,
                'fields': type('obj', (object,), {
                    'emailAddress': getattr(user, 'emailAddress', 'N/A'),
                    'displayName': getattr(user, 'displayName', 'N/A'),
                    'active': 'Yes' if getattr(user, 'active', False) else 'No'
                })
            })
            add_row_to_table(table, user_obj, fields_to_display, color_map)

        print_table(console, table)

        # This module doesn't return ticket IDs, but we'll keep the consistent return type
        return []

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        console.print(f"[yellow]Debug info:[/yellow] {type(e).__name__}: {str(e)}")
    return []

HELP_TEXT = "View team members for a given PROJECT ID (Usage: vt <PROJECT-ID>)"
ALIASES = ["team"]
