import sys
from common.jira_client import get_jira_client
from common.utils import print_header, confirm_action
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from common.cache_vid import vid_cache
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    try:
        jira = get_jira_client()
    except ValueError as e:
        console.print(Panel(f"[bold red]Error:[/bold red] {str(e)}", title="Error", border_style="red", width=110))
        return None

    # Check if a ticket ID was provided as an argument
    if args:
        issue_key = args[0].strip().upper()
    elif current_ticket:
        issue_key = current_ticket
    else:
        issue_key = console.input("[bold cyan]Enter Jira issue key (e.g., PROJ-123):[/bold cyan] ").strip().upper()

    try:
        issue = display_issue(console, jira, issue_key)
        if issue:
            return issue['key']
    except (JIRAError, ValueError) as e:
        console.print(Panel(f"[bold yellow]Unable to fetch Jira issue:[/bold yellow] {str(e)}", title="Warning", border_style="yellow", width=110))
    return None

def display_issue(console, jira, issue_key):
    try:
        issue = vid_cache.get_issue(issue_key)
        
        issue_details = Text()
        issue_details.append(f"Summary: {issue['fields']['summary']}\n")
        issue_details.append(f"Type: {issue['fields']['issuetype']}\n", style="bold blue")
        issue_details.append(f"Status: {issue['fields']['status']}\n", style="bold green")
        issue_details.append(f"Assignee: {issue['fields']['assignee']}\n")
        issue_details.append(f"Reporter: {issue['fields']['reporter']}\n")
        issue_details.append(f"Created: {issue['fields']['created']}\n")
        issue_details.append(f"Updated: {issue['fields']['updated']}\n")
        issue_details.append("\nDescription:\n", style="bold")
        issue_details.append(f"{get_description(jira, issue)}")

        console.print(Panel(issue_details, title=f"Issue Details: {issue['key']}", border_style="cyan", width=110))
        return issue
    except JIRAError as e:
        raise e

def get_description(jira, issue):
    # Try to get the standard description first
    if 'description' in issue['fields'] and issue['fields']['description'] is not None:
        return issue['fields']['description']

    # If standard description is not available, look for a custom field
    custom_fields = [field for field in jira.fields() if 'description' in field['name'].lower()]
    for field in custom_fields:
        if field['id'] in issue['fields'] and issue['fields'][field['id']] is not None:
            return issue['fields'][field['id']]

    return 'No description available'  # Return this if no description field is found

HELP_TEXT = "Show details for a Jira issue"
