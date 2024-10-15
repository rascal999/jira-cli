from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.table import create_jira_table, add_row_to_table, print_table

def perform_jql_search(jql_query, fields_to_display, max_results=None):
    console = Console()
    try:
        jira = get_jira_client()
        console.print(f"[yellow]Executing JQL query:[/yellow] {jql_query}")
        
        if max_results:
            issues = jira.search_issues(jql_query, fields=','.join(fields_to_display), maxResults=max_results)
        else:
            issues = jira.search_issues(jql_query, fields=','.join(fields_to_display))

        if not issues:
            console.print("[yellow]No issues found matching the query.[/yellow]")
            return False

        table = create_jira_table("JQL Search Results", fields_to_display)
        color_map = {}

        for issue in issues:
            add_row_to_table(table, issue, fields_to_display, color_map)

        print_table(console, table)
        return True

    except JIRAError as e:
        console.print(f"[bold red]Error performing JQL search:[/bold red] {str(e)}")
        return False
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        console.print(f"[yellow]JQL query:[/yellow] {jql_query}")
        console.print(f"[yellow]Fields to display:[/yellow] {fields_to_display}")
        return False
