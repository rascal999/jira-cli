from rich.console import Console

console = Console()

def link_issues(issue_manager, current_ticket, arg):
    if not current_ticket:
        console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")
        return

    if not arg:
        console.print("Please provide a ticket ID to link to.", style="yellow")
        return

    try:
        # Fetch the current issue to check existing links
        issue = issue_manager.jira.issue(current_ticket)
        
        # Check if the issues are already linked
        existing_link = next((link for link in issue.fields.issuelinks 
                               if (hasattr(link, 'outwardIssue') and link.outwardIssue.key == arg) or
                                  (hasattr(link, 'inwardIssue') and link.inwardIssue.key == arg)), None)
        
        if existing_link:
            # If already linked, unlink the issues
            issue_manager.jira.delete_issue_link(existing_link.id)
            console.print(f"Unlinked {current_ticket} from {arg}", style="green")
            return
        
        # If not linked, proceed with linking
        link_types = issue_manager.jira.issue_link_types()
        
        if not link_types:
            console.print("No link types available.", style="yellow")
            return

        # Display available link types
        console.print("Available link types:", style="cyan")
        for idx, lt in enumerate(link_types, 1):
            console.print(f"{idx}. {lt.outward} / {lt.inward}", style="white")
        
        # Ask user to choose a link type
        choice = input("Enter the number of the link type you want to use: ")
        try:
            chosen_link_type = link_types[int(choice) - 1]
        except (ValueError, IndexError):
            console.print("Invalid choice. Using the first available link type.", style="yellow")
            chosen_link_type = link_types[0]

        # Create the link
        issue_manager.jira.create_issue_link(
            type=chosen_link_type.name,
            inwardIssue=current_ticket,
            outwardIssue=arg
        )
        console.print(f"Linked {current_ticket} to {arg} with link type '{chosen_link_type.outward}'", style="green")
    except Exception as e:
        console.print(f"Error managing issue link: {str(e)}", style="red")

def execute(cli, arg):
    link_issues(cli.issue_manager, cli.current_ticket, arg)

COMMAND = "link"
HELP = "Link current ticket to specified ticket or unlink if already linked. Usage: /link TICKET_ID"
