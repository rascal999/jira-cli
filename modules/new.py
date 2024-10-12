from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from modules import vid

def run(args, current_ticket=None):
    console = Console()

    if len(args) < 3:
        console.print("[bold red]Error:[/bold red] Insufficient arguments. Usage: new <PROJECT-ID> <TYPE> <SUMMARY>")
        return

    project_id = args[0].upper()
    issue_type = args[1].capitalize()
    summary = ' '.join(args[2:])

    try:
        jira = get_jira_client()

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
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Create a new Jira ticket and display its details (Usage: new <PROJECT-ID> <TYPE> <SUMMARY>)"
