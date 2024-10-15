from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    try:
        jira = get_jira_client()
        source_issue = jira.issue(current_ticket)

        # If no target project is provided, use the current project
        if args:
            target_project = args[0].upper()
        else:
            target_project = source_issue.fields.project.key

        # Prepare the fields for the new issue
        fields = {
            'project': {'key': target_project},
            'summary': source_issue.fields.summary,
            'description': source_issue.fields.description,
            'issuetype': {'name': source_issue.fields.issuetype.name},
        }

        # Copy additional fields if they exist
        if hasattr(source_issue.fields, 'priority'):
            fields['priority'] = {'name': source_issue.fields.priority.name}
        if hasattr(source_issue.fields, 'components'):
            fields['components'] = [{'name': c.name} for c in source_issue.fields.components]
        if hasattr(source_issue.fields, 'labels'):
            fields['labels'] = source_issue.fields.labels

        # Create the new issue
        new_issue = jira.create_issue(fields=fields)

        console.print(f"[bold green]Successfully copied {current_ticket} to {new_issue.key}[/bold green]")

        # Copy comments
        for comment in source_issue.fields.comment.comments:
            jira.add_comment(new_issue, comment.body)

        console.print("[green]Copied all comments[/green]")

        # Copy attachments
        for attachment in source_issue.fields.attachment:
            jira.add_attachment(new_issue, attachment.get())

        console.print("[green]Copied all attachments[/green]")

        # Create a link between the source and new issue
        jira.create_issue_link(
            type="Relates",
            inwardIssue=source_issue.key,
            outwardIssue=new_issue.key
        )

        console.print(f"[green]Created link between {source_issue.key} and {new_issue.key}[/green]")

        return new_issue.key

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

HELP_TEXT = "Copy the current ticket to a target PROJECT (Usage: cp [TARGET_PROJECT])"
ALIASES = ["copy"]