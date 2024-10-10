from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich import box
from datetime import datetime
from rich.table import Table
from rich.console import Console
import hashlib
from jira import JIRA

def display_issue_header(issue, get_field):
    issue_text = Text()
    issue_key = issue.get('key') if isinstance(issue, dict) else issue.key
    issue_text.append(f"{issue_key}: ", style="cyan bold")
    issue_text.append(f"{get_field('summary') or 'No summary available'}\n\n", style="white bold")
    return issue_text

def display_issue_fields(issue, get_field, get_nested_value):
    issue_text = Text()
    fields_to_display = [
        ('Status', 'status'),
        ('Type', 'issuetype'),
        ('Priority', 'priority'),
        ('Assignee', 'assignee'),
        ('Reporter', 'reporter'),
        ('Created', 'created'),
        ('Updated', 'updated'),
    ]

    for display_name, field_name in fields_to_display:
        field_value = get_field(field_name)
        print(f"Field: {field_name}, Raw value: {field_value}")
        try:
            value = get_nested_value(field_value, field_name)
            print(f"Nested value: {value}")
            issue_text.append(f"{display_name}: {value}\n", style="white")
        except Exception as e:
            issue_text.append(f"{display_name}: Error retrieving value\n", style="red")
            print(f"Error processing {field_name}: {str(e)}")

    return issue_text

def display_issue_description(issue, get_field):
    issue_text = Text()
    issue_text.append("\nDescription:\n", style="blue bold")
    issue_text.append(f"{get_field('description') or 'No description provided.'}\n", style="white")
    return issue_text

def display_parent_ticket(issue, get_field, console):
    parent = get_field('parent')
    if parent:
        console.print("\nParent Ticket:", style="blue bold")
        if isinstance(parent, dict):
            parent_key = parent.get('key')
            parent_summary = parent.get('fields', {}).get('summary', 'No summary available')
        else:
            parent_key = getattr(parent, 'key', 'Unknown')
            parent_summary = getattr(parent.fields, 'summary', 'No summary available')
        console.print(f"{parent_key}: {parent_summary}", style="white")

def display_child_tasks(issue, get_field, console, cursor, data_source):
    child_tasks = get_field('child_tasks') or []
    if child_tasks:
        console.print(f"\n{cursor}Child Tasks (from {data_source}):", style="blue bold")
        for child in child_tasks:
            if isinstance(child, dict):
                console.print(f"{child['key']}: {child['fields']['summary']}", style="white")
            else:
                console.print(f"{child.key}: {child.fields.summary}", style="white")

def display_linked_issues(issue, get_field, console):
    links = get_field('issuelinks') or []
    if links:
        console.print("\nLinked Issues:", style="blue bold")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Relation", style="cyan", no_wrap=True)
        table.add_column("Key", style="green")
        table.add_column("Summary", style="white")
        
        for link in links:
            if isinstance(link, dict):
                if 'outwardIssue' in link:
                    related_issue = link['outwardIssue']
                    link_type = link['type']['outward']
                elif 'inwardIssue' in link:
                    related_issue = link['inwardIssue']
                    link_type = link['type']['inward']
                else:
                    continue
                related_key = related_issue['key']
                related_summary = related_issue['fields']['summary']
            else:
                if hasattr(link, 'outwardIssue'):
                    related_issue = link.outwardIssue
                    link_type = link.type.outward
                elif hasattr(link, 'inwardIssue'):
                    related_issue = link.inwardIssue
                    link_type = link.type.inward
                else:
                    continue
                related_key = related_issue.key
                related_summary = related_issue.fields.summary

            table.add_row(link_type, related_key, related_summary)
        
        console.print(table)
    else:
        console.print("\nNo linked issues found.", style="yellow")

def display_subtasks(issue, get_field, console, cursor, data_source):
    subtasks = get_field('subtasks') or []
    if subtasks:
        console.print(f"\n{cursor}Sub-tasks (from {data_source}):", style="blue bold")
        for subtask in subtasks:
            if isinstance(subtask, dict):
                console.print(f"{subtask['key']}: {subtask['fields']['summary']}", style="white")
            else:
                console.print(f"{subtask.key}: {subtask.fields.summary}", style="white")

def display_comments(issue, get_field, console, cursor, jira, format_comment_body, get_color_for_user):
    try:
        if isinstance(issue, dict):
            comments = get_field('comment', {}).get('comments', [])
        else:
            comments = jira.comments(issue.key)

        if comments:
            console.print(f"\n{cursor}Comments:", style="blue bold")
            
            for comment in comments:
                if isinstance(comment, dict):
                    author = comment.get('author', {}).get('displayName', 'Unknown')
                    created = comment.get('created', 'Unknown date')
                    body = comment.get('body', 'No content')
                else:
                    author = comment.author.displayName if comment.author else 'Unknown'
                    created = comment.created
                    body = comment.renderedBody if hasattr(comment, 'renderedBody') else comment.body

                body = format_comment_body(body)

                author_color = get_color_for_user(author)
                
                comment_text = Text()
                comment_text.append(f"{author}", style=f"bold {author_color}")
                comment_text.append(f" - {created}\n\n", style="italic")
                comment_text.append(body)

                comment_panel = Panel(
                    comment_text,
                    border_style=author_color,
                    expand=False
                )
                console.print(comment_panel)
        else:
            console.print(f"\n{cursor}No comments found.", style="yellow")
    except Exception as e:
        console.print(f"\n{cursor}Error fetching comments: {str(e)}", style="red")

def display_issue(self, issue):
    # Determine the data source
    if isinstance(issue, dict):
        cursor = "📁 "  # Cache indicator
        get_field = lambda field, default=None: issue.get('fields', {}).get(field, default)
        data_source = "cache"
    else:
        cursor = "🌐 "  # API indicator
        get_field = lambda field, default=None: getattr(issue.fields, field, default)
        data_source = "API"

    # Display issue details
    self.console.print(f"\n{cursor}Issue Details: {issue.key}", style="bold cyan")
    
    issue_text = display_issue_header(issue, get_field)
    issue_text.append(display_issue_fields(issue, get_field, self.get_nested_value))
    issue_text.append(display_issue_description(issue, get_field))

    panel = Panel(issue_text, title=f"Issue Details: {issue.key}", expand=False, border_style="cyan")
    self.console.print(panel)

    display_parent_ticket(issue, get_field, self.console)
    display_child_tasks(issue, get_field, self.console, cursor, data_source)
    display_linked_issues(issue, get_field, self.console)
    display_subtasks(issue, get_field, self.console, cursor, data_source)
    display_comments(issue, get_field, self.console, cursor, self.jira, self.format_comment_body, self.get_color_for_user)

def get_color_for_string(s):
    """Generate a consistent color based on the input string."""
    hash_object = hashlib.md5(s.encode())
    hash_hex = hash_object.hexdigest()
    return f"#{hash_hex[:6]}"

def display_issues_table(self, issues, title):
    table = Table(title=title)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Summary", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Assignee", style="yellow")

    for index, issue in enumerate(issues):
        key = Text(issue.key, style=get_color_for_string(issue.key.split('-')[0]))
        summary_style = "green" if index % 2 == 0 else "bright_magenta"
        summary = Text(issue.fields.summary, style=summary_style)
        status = Text(issue.fields.status.name, style=get_color_for_string(issue.fields.status.name))
        assignee = Text(issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned", 
                        style=get_color_for_string(issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"))

        table.add_row(key, summary, status, assignee)

    console = Console()
    console.print(table)