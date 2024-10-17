from rich.console import Console
from rich.table import Table
from rich.box import HEAVY_EDGE
from rich.text import Text
from rich.style import Style
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
import hashlib

def get_color_and_emoji_for_assignee(assignee):
    colors = ["red", "green", "blue", "magenta", "cyan", "yellow", "white"]
    emojis = ["🚀", "🌟", "🐼", "🦄", "🍕", "🌈", "🎸", "🍉", "🦋", "🐲", "🌺", "🎨", "🍀", "🦜", "🌮", "🎭", "🦊", "🍎", "🦖", "🎩"]
    if not assignee:
        return "dim white", "❓"
    hash_value = int(hashlib.md5(assignee.encode()).hexdigest(), 16)
    return colors[hash_value % len(colors)], emojis[hash_value % len(emojis)]

def get_status_category(jira, status_name):
    for status_type in jira.statuses():
        if status_type.name == status_name:
            return status_type.statusCategory.name
    return "Unknown"

def sort_statuses(jira, statuses):
    status_order = {"To Do": 0, "In Progress": 1, "Done": 2}
    backlog_statuses = []
    todo_statuses = []
    in_progress_statuses = []
    done_statuses = []
    
    for status in statuses:
        category = get_status_category(jira, status)
        if status.lower() == "backlog":
            backlog_statuses.append(status)
        elif category == "To Do":
            todo_statuses.append(status)
        elif category == "In Progress":
            in_progress_statuses.append(status)
        elif category == "Done":
            done_statuses.append(status)
        else:
            in_progress_statuses.append(status)
    
    return (sorted(todo_statuses) + 
            backlog_statuses + 
            sorted(in_progress_statuses) + 
            sorted(done_statuses))

def run(args, current_ticket=None):
    console = Console()

    if not args:
        console.print("[bold red]Error:[/bold red] Please provide a PROJECT ID or BOARD ID.")
        return []

    project_or_board_id = args[0].upper()

    try:
        jira = get_jira_client()
        
        # Get all active sprints
        all_sprints = jira.sprints(project_or_board_id, state='active')
        
        if not all_sprints:
            console.print(f"[yellow]No active sprints found for {project_or_board_id}.[/yellow]")
            return []

        active_sprint = all_sprints[0]

        # Get all issues in the active sprint
        jql_query = f'sprint = {active_sprint.id} ORDER BY status ASC'
        issues = jira.search_issues(jql_query, maxResults=False)

        # Group issues by epic and status
        epics = {}
        statuses = set()
        epic_summaries = {}
        ticket_ids = []
        assignees = set()
        for issue in issues:
            epic_link = getattr(issue.fields, 'customfield_10014', 'No Epic')  # Adjust field name if needed
            if epic_link and epic_link != 'No Epic' and epic_link not in epic_summaries:
                epic_issue = jira.issue(epic_link)
                epic_summaries[epic_link] = epic_issue.fields.summary
            status = issue.fields.status.name
            if epic_link not in epics:
                epics[epic_link] = {}
            if status not in epics[epic_link]:
                epics[epic_link][status] = []
            epics[epic_link][status].append(issue)
            statuses.add(status)
            ticket_ids.append(issue.key)
            assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
            assignees.add(assignee)

        # Sort statuses
        sorted_statuses = sort_statuses(jira, statuses)

        # Create assignee color and emoji key
        assignee_key = Text()
        assignee_info = {}
        for i, assignee in enumerate(sorted(assignees)):
            color, emoji = get_color_and_emoji_for_assignee(assignee)
            assignee_info[assignee] = (color, emoji)
            assignee_key.append(f"{emoji} ", style=Style(color=color))
            assignee_key.append(f"{assignee}", style="bold")
            if i < len(assignees) - 1:
                assignee_key.append(" | ")

        # Print assignee color and emoji key
        console.print(assignee_key)
        console.print()  # Add a blank line for separation

        # Create and populate the table
        table = Table(title=f"Sprint Board for {project_or_board_id} - {active_sprint.name}", box=HEAVY_EDGE)
        table.add_column("Epic / Status", style="cyan", no_wrap=True)
        for status in sorted_statuses:
            table.add_column(status, style="magenta")

        first_epic = True
        for epic, status_issues in epics.items():
            if not first_epic:
                table.add_section()
            first_epic = False
            
            epic_display = f"{epic}\n{epic_summaries.get(epic, 'No Summary')}" if epic != 'No Epic' else 'No Epic'
            row = [epic_display]
            for status in sorted_statuses:
                cell_content = []
                for issue in status_issues.get(status, []):
                    assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
                    color, emoji = assignee_info[assignee]
                    cell_content.append(Text(f"{emoji} {issue.key}: {issue.fields.summary}", style=color))
                row.append(Text("\n").join(cell_content))
            table.add_row(*row)

        console.print(table)

        return ticket_ids

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        console.print(f"[yellow]Debug info:[/yellow] {type(e).__name__}: {str(e)}")

    return []

HELP_TEXT = "Display current sprint board with epics and statuses (Usage: sprint <PROJECT-ID or BOARD-ID>)"
