from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from common.table import create_jira_table, add_row_to_table, print_table

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        links = issue.fields.issuelinks
        if not links:
            console.print(f"[yellow]No linked issues found for {current_ticket}[/yellow]")
            return

        table = create_jira_table(f"Linked Issues for {current_ticket}", ["Link Type", "Issue Key", "Summary", "Status"])
        color_map = {}

        for link in links:
            if hasattr(link, "outwardIssue"):
                linked_issue = link.outwardIssue
                link_type = link.type.outward
            elif hasattr(link, "inwardIssue"):
                linked_issue = link.inwardIssue
                link_type = link.type.inward
            else:
                continue

            issue_obj = type('obj', (object,), {
                'key': linked_issue.key,
                'fields': type('obj', (object,), {
                    'linktype': link_type,
                    'key': linked_issue.key,
                    'summary': linked_issue.fields.summary,
                    'status': linked_issue.fields.status.name
                })
            })

            add_row_to_table(table, issue_obj, ['linktype', 'key', 'summary', 'status'], color_map)

        print_table(console, table)

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "View linked issues for the current ticket"
ALIASES = ["links"]
