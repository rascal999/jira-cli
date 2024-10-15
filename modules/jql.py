from common.jql import perform_jql_search
from rich.console import Console
from common.jql_filters import save_jql_filter

def run(args, current_ticket=None):
    console = Console()

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a JQL query.")
        return

    jql_query = ' '.join(args)
    fields_to_display = ['key', 'summary', 'status', 'assignee']

    try:
        result = perform_jql_search(jql_query, fields_to_display, max_results=30)
        
        # Only prompt to save if the search was successful
        if result:
            filter_name = console.input("\nEnter a name to save this JQL filter (or press Enter to skip): ").strip()
            if filter_name:
                save_jql_filter(filter_name, jql_query)
                console.print(f"[bold green]JQL filter saved as '{filter_name}'[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

HELP_TEXT = "Perform a JQL query and display results (Usage: jql <JQL query>)"
ALIASES = ["j","search"]
