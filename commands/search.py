from rich.console import Console
from rich.table import Table
from utils import resolve_user_display_name
from jira import JIRAError
from urllib.parse import quote

console = Console()

def execute(cli, arg):
    if arg.startswith('/'):
        # If the argument starts with '/', use it as a text search
        jql = f'text ~ "{arg[1:]}"'
    else:
        # Otherwise, use the input directly as JQL
        jql = arg
    
    search_issues(cli.issue_manager, jql)

def search_issues(issue_manager, query):
    try:
        issues = issue_manager.jira.search_issues(query)
        
        # Generate the JQL query URL
        base_url = issue_manager.jira.client_info()
        encoded_query = quote(query)
        jql_url = f"{base_url}/issues/?jql={encoded_query}"
        
        if issues:
            issue_manager.display_issues_table(issues, f"Search Results for '{query}'")
            console.print(f"\nJQL Query URL: {jql_url}", style="cyan")
        else:
            console.print("No issues found matching the query.", style="yellow")
        
        return issues, jql_url if issues else None
    
    except JIRAError as e:
        if e.status_code == 400:
            console.print("Invalid JQL query. Please check your syntax.", style="red")
            console.print("Examples of valid queries:", style="yellow")
            console.print("  summary ~ \"keyword\"", style="cyan")
            console.print("  project = \"PROJECT\" AND status = \"Open\"", style="cyan")
            console.print("  assignee = currentUser() AND priority = High", style="cyan")
        else:
            console.print(f"Error searching for issues: HTTP {e.status_code} - {e.text}", style="red")
        return [], None
    
    except Exception as e:
        console.print(f"Unexpected error searching for issues: {str(e)}", style="red")
        return [], None

COMMAND = "search"
HELP = "Search for issues using JQL. Use '/text' for text search. Example: /s /keyword or /s project = PROJECT"