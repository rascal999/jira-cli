from common.jql import perform_jql_search
from common.jira_client import get_jira_client
from rich.console import Console

def run(args=None, current_ticket=None):
    console = Console()
    try:
        jira = get_jira_client()
        current_user = jira.myself()
        
        if 'name' in current_user:
            username = current_user['name']
        elif 'displayName' in current_user:
            username = current_user['displayName']
        elif 'emailAddress' in current_user:
            username = current_user['emailAddress']
        else:
            console.print("[bold red]Error:[/bold red] Unable to determine current user's name or email.")
            return []

        jql_query = f'assignee = "{username}" OR reporter = "{username}" ORDER BY updated DESC'
        fields_to_display = ['key', 'summary', 'status', 'created']
        
        return perform_jql_search(jql_query, fields_to_display, max_results=10)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("[yellow]Debug info:[/yellow]")
        console.print(f"Current user data: {current_user}")
    return []

HELP_TEXT = "Display recent tickets assigned to current user"
ALIASES = ["top"]
