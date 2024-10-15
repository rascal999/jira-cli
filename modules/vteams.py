from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.table import create_jira_table, add_row_to_table, print_table

def run(args, current_ticket=None):
    console = Console()

    try:
        jira = get_jira_client()
        
        # Get all teams
        teams = jira.groups()

        if not teams:
            console.print("[yellow]No teams found in Jira.[/yellow]")
            return

        fields_to_display = ['name', 'member_count']
        table = create_jira_table("Jira Teams", fields_to_display)
        color_map = {}

        for team in teams:
            team_obj = type('obj', (object,), {
                'key': team,
                'fields': type('obj', (object,), {
                    'name': team,
                    'member_count': len(jira.group_members(team))
                })
            })
            add_row_to_table(table, team_obj, fields_to_display, color_map)

        print_table(console, table)

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        console.print(f"[yellow]Debug info:[/yellow] {type(e).__name__}: {str(e)}")

HELP_TEXT = "View all teams in Jira"
ALIASES = ["teams"]