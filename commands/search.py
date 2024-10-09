from rich.console import Console
from rich.table import Table
from utils import resolve_user_display_name
from jira import JIRAError
from urllib.parse import quote

console = Console()

def search_issues(issue_manager, query):
    try:
        issues = issue_manager.jira.search_issues(query)
        
        # Generate the JQL query URL
        base_url = issue_manager.jira.client_info()
        encoded_query = quote(query)
        jql_url = f"{base_url}/issues/?jql={encoded_query}"
        
        if issues:
            display_search_results(issues)
            console.print(f"\nJQL Query URL: {jql_url}", style="cyan")
        else:
            console.print("No issues found matching the query.", style="yellow")
        
        return issues, jql_url if issues else None
    
    except JIRAError as e:
        if e.status_code == 400:
            console.print("Invalid JQL query. Please check your syntax.", style="red")
            console.print("Examples of valid queries:", style="yellow")
            console.print("  text ~ \"keyword\"", style="cyan")
            console.print("  project = \"PROJECT\" AND status = \"Open\"", style="cyan")
            console.print("  assignee = currentUser() AND priority = High", style="cyan")
        else:
            console.print(f"Error searching for issues: HTTP {e.status_code}", style="red")
        return [], None
    
    except Exception as e:
        console.print("Unexpected error searching for issues.", style="red")
        return [], None

def display_search_results(issues):
    table = Table(title="Search Results")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Summary", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Assignee", style="yellow")

    for issue in issues:
        assignee = resolve_user_display_name(issue.fields.assignee)
        table.add_row(issue.key, issue.fields.summary, issue.fields.status.name, assignee)

    console.print(table)

def get_recent_issues(issue_manager):
    jql = "order by created DESC"
    issues = issue_manager.search_issues(jql)
    for issue in list(issues)[:10]:  # Limit to first 10 issues
        print(f"{issue.key}: {issue.fields.summary}")
