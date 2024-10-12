import os
from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
import glob

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a file path to attach.")
        return

    file_path = args[0]

    if not os.path.exists(file_path):
        console.print(f"[bold red]Error:[/bold red] File not found: {file_path}")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        with open(file_path, 'rb') as file:
            jira.add_attachment(issue=issue, attachment=file, filename=os.path.basename(file_path))

        console.print(f"[bold green]Successfully attached {os.path.basename(file_path)} to {current_ticket}[/bold green]")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")

def complete_file_path(text, line, begidx, endidx):
    before_arg = line.rfind(" ", 0, begidx)
    if before_arg == -1:
        return  # arg not found

    fixed = line[before_arg+1:begidx]  # fixed portion of the arg
    arg = line[before_arg+1:endidx]
    pattern = arg + '*'

    completions = []
    for path in glob.glob(pattern):
        if os.path.isdir(path):
            completions.append(path + os.path.sep)
        else:
            completions.append(path)

    return [c[len(fixed):] for c in completions]

HELP_TEXT = "Attach a file to the current ticket (Usage: attach <FILE>)"

