from common.jql import perform_jql_search
from rich.console import Console
from common.last_jql import set_last_jql

def run(args, current_ticket=None):
    console = Console()

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a JQL query.")
        return []

    jql_query = ' '.join(args)
    fields_to_display = ['key', 'summary', 'status', 'assignee']

    try:
        ticket_ids = perform_jql_search(jql_query, fields_to_display, max_results=30)
        set_last_jql(jql_query)  # Store the JQL query
        return ticket_ids
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return []

HELP_TEXT = "Perform a JQL query and display results (Usage: jql <JQL query>)"
ALIASES = ["j","search"]
