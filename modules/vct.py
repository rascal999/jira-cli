from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.table import create_jira_table, add_row_to_table, print_table

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return []

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        jql_query = f'parent = {current_ticket} ORDER BY created DESC'
        child_issues = jira.search_issues(jql_query)

        if not child_issues:
            console.print(f"[yellow]No child tasks found for {current_ticket}.[/yellow]")
            return []

        fields_to_display = ['key', 'summary', 'status', 'assignee']
        table = create_jira_table(f"Child Tasks for {current_ticket}", fields_to_display)
        color_map = {}

        ticket_ids = []
        for child in child_issues:
            add_row_to_table(table, child, fields_to_display, color_map)
            ticket_ids.append(child.key)

        print_table(console, table)
        return ticket_ids

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")
    return []

HELP_TEXT = "View child tasks for the current ticket"
