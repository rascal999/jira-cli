from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if args:
        issue_key = args[0].strip().upper()
    elif current_ticket:
        issue_key = current_ticket
    else:
        console.print("[bold red]Error:[/bold red] No ticket specified and no current ticket set.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(issue_key)

        # Get all fields for the issue
        fields = issue.raw['fields']

        # Create a Text object to store all field information
        issue_details = Text()

        # Add standard fields that are always visible
        standard_fields = ['summary', 'description', 'issuetype', 'status', 'priority', 'assignee', 'reporter', 'created', 'updated']
        for field in standard_fields:
            if field in fields:
                value = fields[field]
                if isinstance(value, dict) and 'name' in value:
                    value = value['name']
                elif isinstance(value, dict) and 'displayName' in value:
                    value = value['displayName']
                issue_details.append(f"{field.capitalize()}: {value}\n", style="bold")

        # Add custom fields that have a value (assuming they're visible)
        for field_id, value in fields.items():
            if field_id.startswith('customfield_') and value:
                field_name = jira.field(field_id)['name']
                if isinstance(value, dict) and 'value' in value:
                    value = value['value']
                elif isinstance(value, list):
                    value = ', '.join([str(v) for v in value])
                issue_details.append(f"{field_name}: {value}\n", style="cyan")

        console.print(Panel(issue_details, title=f"Issue Details: {issue_key}", border_style="green", expand=False))

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "View detailed information for a Jira issue, including visible fields"
