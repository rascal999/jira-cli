from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def add_comment(issue_manager, current_ticket, arg):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    if not arg:
        console.print("Please provide a comment to add.", style="yellow")
        return

    try:
        issue = issue_manager.jira.issue(current_ticket)
        comment = issue_manager.jira.add_comment(issue, arg)
        
        # Display the added comment
        author = comment.author.displayName
        created = comment.created
        
        comment_text = Text()
        comment_text.append(comment.body)
        
        panel = Panel(
            comment_text,
            title=f"{author} - {created}",
            title_align="left",
            border_style="green",
            expand=False
        )
        
        console.print("\nComment added successfully:", style="green")
        console.print(panel)
        
    except Exception as e:
        console.print(f"Error adding comment to {current_ticket}: {str(e)}", style="red")

def execute(cli, arg):
    add_comment(cli.issue_manager, cli.current_ticket, arg)

COMMAND = "comment"
HELP = "Add a comment to the current ticket. Usage: /comment Your comment here."
