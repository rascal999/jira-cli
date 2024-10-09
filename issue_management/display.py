from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich import box
from datetime import datetime
from rich.table import Table
from rich.console import Console
import hashlib

def display_issue(self, issue):
    try:
        issue_text = Text()
        issue_text.append(f"{issue.key}: ", style="cyan bold")
        issue_text.append(f"{issue.fields.summary}\n\n", style="white bold")

        issue_text.append("Status: ", style="blue")
        issue_text.append(f"{getattr(issue.fields.status, 'name', 'Unknown')}\n", style=self.get_status_style(getattr(issue.fields.status, 'name', 'Unknown')))

        issue_text.append("Type: ", style="blue")
        issue_text.append(f"{getattr(issue.fields.issuetype, 'name', 'Unknown')}\n", style="magenta")

        issue_text.append("Priority: ", style="blue")
        issue_text.append(f"{getattr(issue.fields.priority, 'name', 'Unknown')}\n", style="yellow")

        issue_text.append("Assignee: ", style="blue")
        assignee = getattr(issue.fields, 'assignee', None)
        assignee_name = assignee.displayName if assignee else "Unassigned"
        issue_text.append(f"{assignee_name}\n", style="green")

        issue_text.append("Reporter: ", style="blue")
        reporter = getattr(issue.fields, 'reporter', None)
        reporter_name = reporter.displayName if reporter else "Unknown"
        issue_text.append(f"{reporter_name}\n", style="green")

        issue_text.append("Created: ", style="blue")
        issue_text.append(f"{getattr(issue.fields, 'created', 'Unknown')}\n", style="white")

        issue_text.append("Updated: ", style="blue")
        issue_text.append(f"{getattr(issue.fields, 'updated', 'Unknown')}\n\n", style="white")

        issue_text.append("Description:\n", style="blue bold")
        issue_text.append(f"{getattr(issue.fields, 'description', 'No description provided.')}\n", style="white")

        panel = Panel(issue_text, title=f"Issue Details: {issue.key}", expand=False, border_style="cyan")
        self.console.print(panel)

        # Display parent ticket
        if hasattr(issue.fields, 'parent'):
            parent = issue.fields.parent
            self.console.print(f"\nParent: {parent.key} - {parent.fields.summary}", style="cyan")

        # Display linked tickets
        links = getattr(issue.fields, 'issuelinks', [])
        if links:
            self.console.print("\nLinked Issues:", style="cyan")
            for link in links:
                if hasattr(link, 'outwardIssue'):
                    linked_issue = link.outwardIssue
                    link_type = link.type.outward
                elif hasattr(link, 'inwardIssue'):
                    linked_issue = link.inwardIssue
                    link_type = link.type.inward
                else:
                    continue
                self.console.print(f"  {link_type}: {linked_issue.key} - {linked_issue.fields.summary}")

        # Display sub-tasks
        subtasks = getattr(issue.fields, 'subtasks', [])
        if subtasks:
            self.console.print("\nSub-tasks:", style="cyan")
            for subtask in subtasks:
                self.console.print(f"  {subtask.key} - {subtask.fields.summary}")

        # Display comments
        self.display_comments(issue.key)
    except AttributeError as e:
        print(f"Error displaying issue details: {e}")
        print(f"Issue key: {issue.key}")
        print("Some fields may be missing or inaccessible.")

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
