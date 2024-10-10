from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def show_comments(issue_manager, current_ticket, arg):
    ticket_to_show = arg if arg else current_ticket

    if not ticket_to_show:
        console.print("No ticket specified and no ticket currently focused.", style="yellow")
        return

    try:
        # Use the cache to get comments
        comments = issue_manager.cache_manager.get_comments(ticket_to_show)

        if comments:
            console.print(f"\nComments for {ticket_to_show}:", style="blue bold")
            
            for comment in comments:
                author = comment['author']['displayName'] if comment['author'] else 'Unknown'
                created = comment['created']
                body = comment['body']

                formatted_body = issue_manager.format_comment_body(body)

                author_color = issue_manager.get_color_for_user(author)
                
                comment_text = Text()
                comment_text.append(f"{author}", style=f"bold {author_color}")
                comment_text.append(f" - {created}\n\n")
                comment_text.append(formatted_body)

                comment_panel = Panel(
                    comment_text,
                    border_style=author_color,
                    expand=False,
                    width=110
                )
                console.print(comment_panel)
        else:
            console.print(f"\nNo comments found for {ticket_to_show}.", style="yellow")
    except Exception as e:
        console.print(f"\nError fetching comments for {ticket_to_show}: {str(e)}", style="red")

def execute(cli, arg):
    show_comments(cli.issue_manager, cli.current_ticket, arg)

COMMAND = "sc"
HELP = "Show comments for the current ticket or specified ticket. Usage: /sc [TICKET-ID]"