import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.align import Align
from common.jira_client import get_jira_client
from common.cache_vid import vid_cache
from common.cache_users import user_cache
from jira.exceptions import JIRAError
import hashlib

def run(args, current_ticket=None):
    console = Console()

    try:
        jira = get_jira_client()
    except ValueError as e:
        console.print(Panel(f"[bold red]Error:[/bold red] {str(e)}", title="Error", border_style="red", width=110))
        return

    # Check if a ticket ID was provided as an argument
    if args:
        issue_key = args[0].strip().upper()
    elif current_ticket:
        issue_key = current_ticket
    else:
        issue_key = console.input("[bold cyan]Enter Jira issue key (e.g., PROJ-123):[/bold cyan] ").strip().upper()

    try:
        display_comments(console, jira, issue_key)
    except JIRAError as e:
        console.print(Panel(f"[bold yellow]Unable to fetch Jira issue:[/bold yellow] {str(e)}", title="Warning", border_style="yellow", width=110))

def display_comments(console, jira, issue_key):
    try:
        issue = jira.issue(issue_key)
        comments = issue.fields.comment.comments

        if not comments:
            console.print(Panel(f"[bold yellow]No comments found for issue {issue_key}[/bold yellow]", border_style="yellow", width=110))
            return

        for comment in comments:
            comment_text = Text()
            author_name = comment.author.displayName
            author_color = get_color_for_author(author_name)
            
            # Resolve user mentions in the comment body with colors
            resolved_body = user_cache.resolve_user_mentions(comment.body, get_color_for_author)
            
            # Replace the placeholders with colored mentions
            import re
            body_parts = re.split(r'<<USER_MENTION:([^:]+):([^>]+)>>', resolved_body)
            for i, part in enumerate(body_parts):
                if i % 3 == 0:
                    comment_text.append(part)
                elif i % 3 == 1:
                    name = body_parts[i]
                    color = body_parts[i+1]
                    comment_text.append(f"@{name}", style=color)

            # Create a panel with left-aligned content and title
            panel = Panel(
                Align.left(comment_text),
                title=f"{author_name} - {comment.created}",
                border_style=author_color,
                width=110,
                title_align="left"  # This aligns the title to the left
            )
            console.print(panel)

    except JIRAError as e:
        raise e

def get_color_for_author(author_name):
    hash_value = hashlib.md5(author_name.encode()).hexdigest()
    r = int(hash_value[:2], 16) % 256
    g = int(hash_value[2:4], 16) % 256
    b = int(hash_value[4:6], 16) % 256
    return f"rgb({r},{g},{b})"

HELP_TEXT = "View comments for a Jira issue"