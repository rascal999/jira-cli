from rich.console import Console
from rich.table import Table
from rich.text import Text
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from modules import vid

def get_valid_issue_types():
    try:
        jira = get_jira_client()
        issue_types = jira.issue_types()
        # Sort issue types alphabetically and remove duplicates
        unique_sorted_types = sorted(set(issue_type.name for issue_type in issue_types))
        # Create a 2D list with 3 columns
        return [unique_sorted_types[i:i+3] for i in range(0, len(unique_sorted_types), 3)]
    except Exception:
        return [["Unable to fetch issue types"]]

def run(args, current_ticket=None):
    console = Console()

    if len(args) == 0:
        console.print("[bold cyan]Usage:[/bold cyan] new <PROJECT-ID> <TYPE> <SUMMARY>")
        console.print("\n[bold cyan]Valid issue types:[/bold cyan]")
        
        table = Table(show_header=False, box=None)
        for i, row in enumerate(get_valid_issue_types()):
            color = "cyan" if i % 2 == 0 else "yellow"
            styled_row = [Text(str(issue_type), style=color) for issue_type in row]
            table.add_row(*styled_row)
        console.print(table)
        return

    if len(args) < 3:
        console.print("[bold red]Error:[/bold red] Insufficient arguments. Usage: new <PROJECT-ID> <TYPE> <SUMMARY>")
        return

    project_id = args[0].upper()
    issue_type = ' '.join(args[1:-1])  # Join all words between project_id and summary
    summary = args[-1]

    try:
        jira = get_jira_client()

        # Verify if the issue type exists
        valid_types = [t.name for t in jira.issue_types()]
        if issue_type not in valid_types:
            console.print(f"[bold red]Error:[/bold red] Invalid issue type '{issue_type}'.")
            console.print("Valid issue types:")
            table = Table(show_header=False, box=None)
            for i, row in enumerate(get_valid_issue_types()):
                color = "cyan" if i % 2 == 0 else "green"
                styled_row = [Text(str(t), style=color) for t in row]
                table.add_row(*styled_row)
            console.print(table)
            return

        # Create the issue
        new_issue = jira.create_issue(
            project=project_id,
            summary=summary,
            issuetype={'name': issue_type}
        )

        console.print(f"[bold green]Success:[/bold green] Created new issue {new_issue.key}")
        vid.run([new_issue.key])

        # Return the new issue key so it can be set as the current ticket
        return new_issue.key

    except JIRAError as e:
        console.print(f"[bold red]Error creating issue:[/bold red] {str(e)}")
        if 'errors' in e.response.text:
            import json
            errors = json.loads(e.response.text)['errors']
            for field, error in errors.items():
                console.print(f"[red]{field}: {error}[/red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Create a new Jira ticket and display its details (Usage: new <PROJECT-ID> <TYPE> <SUMMARY>)"
