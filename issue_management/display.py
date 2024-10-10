from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich import box
from datetime import datetime
from rich.table import Table
from rich.console import Console
import hashlib
from jira import JIRA

def display_issue(self, issue):
    # Determine the data source
    if isinstance(issue, dict):
        cursor = "📁 "  # Cache indicator
        get_field = lambda field, default=None: issue.get('fields', {}).get(field, default)
        child_tasks = issue.get('child_tasks', [])
        data_source = "cache"
        issuetype = get_field('issuetype', {}).get('name', '').lower()
        issue_key = issue.get('key')
    else:
        cursor = "🌐 "  # API indicator
        get_field = lambda field, default=None: getattr(issue.fields, field, default)
        issuetype = getattr(get_field('issuetype'), 'name', '').lower()
        child_tasks = self.get_epic_children(issue.key) if issuetype == 'epic' else []
        data_source = "API"
        issue_key = issue.key

    # Display issue details
    self.console.print(f"\n{cursor}Issue Details: {issue_key}", style="bold cyan")
    
    issue_text = Text()
    issue_text.append(f"{issue_key}: ", style="cyan bold")
    issue_text.append(f"{get_field('summary') or 'No summary available'}\n\n", style="white bold")

    def get_nested_value(obj, key):
        if isinstance(obj, dict):
            if key in ['reporter', 'assignee']:
                return obj.get('displayName') or obj.get('name') or str(obj)
            return obj.get('name') or obj.get(key) or str(obj)
        elif hasattr(obj, 'raw'):
            return get_nested_value(obj.raw, key)
        elif hasattr(obj, key):
            return getattr(obj, key)
        elif hasattr(obj, 'displayName'):
            return obj.displayName
        return str(obj)

    for field_name, field_label in [
        ('status', 'Status'),
        ('issuetype', 'Type'),
        ('priority', 'Priority'),
        ('assignee', 'Assignee'),
        ('reporter', 'Reporter'),
        ('created', 'Created'),
        ('updated', 'Updated')
    ]:
        field_value = get_field(field_name)
        if field_value:
            issue_text.append(f"{field_label}: ", style="blue")
            issue_text.append(f"{get_nested_value(field_value, field_name)}\n", style="white")

    issue_text.append("\nDescription:\n", style="blue bold")
    issue_text.append(f"{get_field('description') or 'No description provided.'}\n", style="white")

    panel = Panel(issue_text, title=f"Issue Details: {issue_key}", expand=False, border_style="cyan")
    self.console.print(panel)

    # Display parent ticket
    parent = get_field('parent')
    if parent:
        self.console.print("\nParent Ticket:", style="blue bold")
        if isinstance(parent, dict):
            parent_key = parent.get('key')
            parent_summary = parent.get('fields', {}).get('summary', 'No summary available')
        else:
            parent_key = getattr(parent, 'key', 'Unknown')
            parent_summary = getattr(parent.fields, 'summary', 'No summary available')
        self.console.print(f"{parent_key}: {parent_summary}", style="white")

    # Display child tasks (if any)
    child_tasks = get_field('child_tasks') or []
    if child_tasks:
        self.console.print(f"\n{cursor}Child Tasks (from {data_source}):", style="blue bold")
        for child in child_tasks:
            if isinstance(child, dict):
                # Child task from cache
                self.console.print(f"{child['key']}: {child['fields']['summary']}", style="white")
            else:
                # Live Jira child task object
                self.console.print(f"{child.key}: {child.fields.summary}", style="white")

    # Display linked issues
    links = get_field('issuelinks') or []
    if links:
        self.console.print("\nLinked Issues:", style="blue bold")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Relation", style="cyan", no_wrap=True)
        table.add_column("Key", style="green")
        table.add_column("Summary", style="white")
        
        for link in links:
            if isinstance(link, dict):
                # Handle cached issue links
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
                # Handle Jira issue link objects
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
        
        self.console.print(table)
    else:
        self.console.print("\nNo linked issues found.", style="yellow")

    # Display sub-tasks (if any)
    subtasks = get_field('subtasks') or []
    if subtasks:
        self.console.print(f"\n{cursor}Sub-tasks (from {data_source}):", style="blue bold")
        for subtask in subtasks:
            if isinstance(subtask, dict):
                # Subtask from cache
                self.console.print(f"{subtask['key']}: {subtask['fields']['summary']}", style="white")
            else:
                # Live Jira subtask object
                self.console.print(f"{subtask.key}: {subtask.fields.summary}", style="white")

    # Display comments
    try:
        if isinstance(issue, dict):
            # Issue is from cache
            comments = get_field('comment', {}).get('comments', [])
        else:
            # Issue is a live Jira object
            # Fetch comments without using maxResults
            comments = self.jira.comments(issue.key)

        if comments:
            self.console.print(f"\n{cursor}Comments:", style="blue bold")
            
            for comment in comments:
                if isinstance(comment, dict):
                    # Comment from cache
                    author = comment.get('author', {}).get('displayName', 'Unknown')
                    created = comment.get('created', 'Unknown date')
                    body = comment.get('body', 'No content')
                else:
                    # Live Jira comment object
                    author = comment.author.displayName if comment.author else 'Unknown'
                    created = comment.created
                    body = comment.renderedBody if hasattr(comment, 'renderedBody') else comment.body

                # Resolve user mentions in the comment body
                body = self.format_comment_body(body)

                author_color = self.get_color_for_user(author)
                
                comment_text = Text()
                comment_text.append(f"{author}", style=f"bold {author_color}")
                comment_text.append(f" - {created}\n\n", style="italic")
                comment_text.append(body)

                comment_panel = Panel(
                    comment_text,
                    border_style=author_color,
                    expand=False
                )
                self.console.print(comment_panel)
        else:
            self.console.print(f"\n{cursor}No comments found.", style="yellow")
    except Exception as e:
        self.console.print(f"\n{cursor}Error fetching comments: {str(e)}", style="red")

    except Exception as e:
        import traceback
        self.console.print(f"Error displaying issue details for {issue_key}: {str(e)}", style="red")
        self.console.print("Error details:", style="red")
        self.console.print(traceback.format_exc(), style="red")

def display_comments(self, issue_key):
    try:
        issue = self.jira.issue(issue_key)
        comments = issue.fields.comment.comments
        if comments:
            self.console.print("\nComments:", style="cyan bold")
            for comment in comments:
                author = comment.author.displayName
                created = datetime.fromisoformat(comment.created.replace('Z', '+00:00'))
                created_str = created.strftime('%Y-%m-%d %H:%M:%S')
                author_color = self.get_color_for_user(author)
                
                comment_text = Text()
                comment_text.append(self.format_comment_body(comment.body))
                
                panel = Panel(
                    comment_text,
                    border_style=author_color,
                    expand=False,
                    width=110,
                    title=f"{author} - {created_str}",
                    title_align="left"
                )
                self.console.print(panel)
                self.console.print()  # Add a blank line between comments
    except Exception as e:
        self.console.print(f"Error fetching comments: {str(e)}", style="red")

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