#!/usr/bin/env python3

import argparse
import cmd
import readline
from issue_management import IssueManager
from auth import get_jira_client
import openai  # You'll need to install this package
from colorama import init, Fore, Style
from tabulate import tabulate
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import os

# Initialize colorama
init(autoreset=True)

class JiraCLI(cmd.Cmd):
    def __init__(self, issue_manager):
        super().__init__()
        self.issue_manager = issue_manager
        self.current_ticket = None
        self.console = Console()
        self.update_prompt()
        self.history_file = os.path.expanduser('~/.jira_cli_history')
        self.load_history()

    def load_history(self):
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)

    def save_history(self):
        readline.write_history_file(self.history_file)

    def update_prompt(self, issue=None):
        if self.current_ticket:
            if not issue:
                issue = self.issue_manager.fetch_issue(self.current_ticket)
            if issue:
                project_key = self.current_ticket.split('-')[0]
                project_color = self.issue_manager.get_project_color(project_key)
                color_code = self.get_ansi_color_code(project_color)
                summary = issue.fields.summary
                self.prompt = f"\001{color_code}\002{self.current_ticket}\001\033[0m\002 - {summary}> "
            else:
                self.prompt = f"{self.current_ticket}> "
        else:
            self.prompt = "Jira> "

    def get_ansi_color_code(self, color_name):
        color_map = {
            "cyan": "\033[36m",
            "magenta": "\033[35m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "red": "\033[31m",
            "purple": "\033[35m",
            "bright_cyan": "\033[96m",
            "bright_magenta": "\033[95m",
            "bright_green": "\033[92m",
            "bright_yellow": "\033[93m",
            "bright_blue": "\033[94m",
            "bright_red": "\033[91m",
            "bright_black": "\033[90m",
            "bright_white": "\033[97m"
        }
        return color_map.get(color_name, "\033[0m")  # Default to reset if color not found

    def complete(self, text, state):
        if text.startswith('@'):
            suggestions = self.issue_manager.get_user_suggestions(text[1:])
            if state < len(suggestions):
                return '@' + suggestions[state]
        return None

    def do_h(self, arg):
        """Show help message."""
        console = Console()
        
        help_text = Text()
        help_text.append("Jira CLI Help\n\n", style="bold")
        help_text.append("Available Commands:\n\n", style="bold underline")
        
        commands = [
            ("/h", "Show this help message."),
            ("/q", "Quit the program."),
            ("/c", "Add a comment to the last ticket. Usage: /c Your comment here."),
            ("/s", "Enter JQL mode to execute a JQL query."),
            ("/d TICKET", "Delete a ticket. Usage: /d TICKET_ID"),
            ("/r", "Display top 10 recently updated tickets reported by you."),
            ("/t [TICKET]", "Display issue tree starting from current or specified ticket."),
            ("/n", "Create a new ticket under the current ticket (epic or task), or create a new epic if no ticket is focused."),
            ("/l TICKET", "Link current ticket to specified ticket as 'Relates to'."),
            ("/e", "List all epics reported by you."),
            ("/x", "Clear the current focused ticket."),
            ("/u", "Update the description of the currently focused ticket."),
            ("/p", "Change focus to parent ticket and display its details."),
            ("/i", "Ask a question to ChatGPT. Usage: /i Your question here."),
            ("/a SUMMARY", "Rename the summary of the currently focused ticket. Usage: /a New summary here.")
        ]
        
        for cmd, desc in commands:
            help_text.append(f"{cmd}", style="cyan bold")
            help_text.append(f" - {desc}\n")
        
        help_text.append("\n", style="bold")
        help_text.append("Type a ticket ID or search string to display ticket information or search results.\n\n", style="italic")
        help_text.append("When a ticket is focused, press [Tab] to display possible statuses above the prompt. ", style="yellow")
        help_text.append("Type the status name and press [Enter] to update the ticket to the selected status.", style="yellow")
        
        console.print(help_text)

    def do_q(self, arg):
        """Quit the program."""
        print("Goodbye!")
        return True

    def do_c(self, arg):
        """Add a comment to the current ticket."""
        if self.current_ticket:
            self.issue_manager.add_comment(self.current_ticket, arg)
        else:
            self.console.print("No ticket currently focused. Use a ticket ID first.", style="yellow")

    def default(self, line):
        """Handle ticket ID, search string input, or commands."""
        if line.startswith('/'):
            cmd = line[1:]  # Remove the leading '/'
            if hasattr(self, 'do_' + cmd):
                return getattr(self, 'do_' + cmd)(None)
            else:
                self.console.print(f"Unknown command: {line}", style="yellow")
                self.console.print("Type '/h' for help.", style="yellow")
                return

        issue = self.issue_manager.fetch_issue(line)
        if issue:
            self.current_ticket = line
            self.update_prompt()
            self.issue_manager.display_issue(issue)
        else:
            self.console.print(f"No issue found with key {line}. Treating as search string.", style="yellow")
            self.issue_manager.search_issues(f'text ~ "{line}"')

    def do_r(self, arg):
        """Show recently updated issues."""
        self.issue_manager.get_recent_issues()
        return False  # Indicate that we want to continue the command loop

    def do_s(self, arg):
        """Search for issues using JQL."""
        if not arg:
            print("Please provide a JQL query.")
            return
        self.issue_manager.search_issues(arg)

    def do_d(self, arg):
        """Delete a ticket."""
        if not arg:
            self.console.print("Please provide a ticket ID to delete.", style="yellow")
            return

        deleted = self.issue_manager.delete_issue(arg)
        if deleted:
            if self.current_ticket == arg:
                self.current_ticket = None
                self.update_prompt()
                self.console.print("Unfocused deleted ticket.", style="green")

    def do_t(self, arg):
        """Display issue tree starting from current or specified ticket."""
        ticket = arg if arg else self.current_ticket
        if ticket:
            self.issue_manager.display_issue_tree(ticket)
        else:
            self.console.print("No ticket specified or currently focused.", style="yellow")

    def do_n(self, arg):
        """Create a new ticket under the current ticket (epic or task), or create a new epic if no ticket is focused."""
        parent = self.current_ticket
        new_issue = self.issue_manager.create_new_issue(parent)
        if new_issue:
            self.current_ticket = new_issue.key
            self.update_prompt()
            self.issue_manager.display_issue(new_issue)

    def do_l(self, arg):
        """Link current ticket to specified ticket as 'Relates to'."""
        if self.current_ticket:
            self.issue_manager.link_issues(self.current_ticket, arg, "Relates to")
        else:
            print("No ticket currently focused. Use a ticket ID first.")

    def do_e(self, arg):
        """List all epics reported by you."""
        self.issue_manager.get_user_epics()

    def do_x(self, arg):
        """Clear the current focused ticket."""
        self.current_ticket = None
        self.update_prompt()
        self.clear_screen()
        self.console.print("Cleared current ticket focus.", style="green")

    def do_u(self, arg):
        """Update the description of the currently focused ticket."""
        if self.current_ticket:
            new_description = input("Enter new description: ")
            self.issue_manager.update_issue_description(self.current_ticket, new_description)
        else:
            print("No ticket currently focused. Use a ticket ID first.")

    def do_p(self, arg):
        """Change focus to parent ticket and display its details."""
        if self.current_ticket:
            parent = self.issue_manager.get_parent_issue(self.current_ticket)
            if parent:
                self.current_ticket = parent.key
                self.issue_manager.display_issue(parent)
            else:
                print("No parent ticket found.")
        else:
            print("No ticket currently focused. Use a ticket ID first.")

    def do_i(self, arg):
        """Ask a question to ChatGPT."""
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": arg}]
        )
        print(response.choices[0].message.content)

    def do_a(self, arg):
        """Rename the summary of the currently focused ticket."""
        if self.current_ticket:
            self.issue_manager.update_issue_summary(self.current_ticket, arg)
        else:
            print("No ticket currently focused. Use a ticket ID first.")

    def default(self, line):
        """Handle ticket ID, search string input, or commands."""
        if line.startswith('/'):
            cmd = line[1:]  # Remove the leading '/'
            if hasattr(self, 'do_' + cmd):
                return getattr(self, 'do_' + cmd)(None)
            else:
                self.console.print(f"Unknown command: {line}", style="yellow")
                self.console.print("Type '/h' for help.", style="yellow")
                return

        issue = self.issue_manager.fetch_issue(line)
        if issue:
            self.current_ticket = line
            self.update_prompt()
            self.issue_manager.display_issue(issue)
        else:
            self.console.print(f"No issue found with key {line}. Treating as search string.", style="yellow")
            self.issue_manager.search_issues(f'text ~ "{line}"')

    def completedefault(self, text, line, begidx, endidx):
        """Provide tab completion for status updates."""
        if self.current_ticket:
            statuses = self.issue_manager.get_available_statuses(self.current_ticket)
            return [s for s in statuses if s.lower().startswith(text.lower())]
        return []

    def postcmd(self, stop, line):
        """Handle status updates and ticket focusing."""
        if line.startswith('/'):
            return stop  # Don't process commands further

        if self.current_ticket:
            available_statuses = self.issue_manager.get_available_statuses(self.current_ticket)
            if line in available_statuses:
                self.issue_manager.update_issue_status(self.current_ticket, line)
        return stop

    def focus_on_issue(self, issue):
        self.current_ticket = issue.key
        self.update_prompt(issue)
        # Remove the display_issue call from here

    def emptyline(self):
        """Handle empty line input."""
        if self.prompt == "Jira> ":
            self.do_h(None)
        elif self.current_ticket:
            issue = self.issue_manager.fetch_issue(self.current_ticket)
            if issue:
                self.issue_manager.display_issue(issue)
            else:
                self.console.print(f"Unable to fetch details for {self.current_ticket}", style="yellow")

    def precmd(self, line):
        """Preprocess the input line."""
        if line.startswith('/'):
            return line[1:]  # Remove the leading '/'
        return line

    def clear_screen(self):
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

def main():
    parser = argparse.ArgumentParser(description="Jira CLI Tool")
    parser.add_argument("ticket", nargs="?", help="Jira ticket key (e.g., EXAMPLE-123)")
    args = parser.parse_args()

    jira_client = get_jira_client()
    issue_manager = IssueManager(jira_client)

    cli = JiraCLI(issue_manager)
    
    if args.ticket:
        cli.onecmd(args.ticket)
    else:
        print("No initial ticket or search string provided. Starting interactive shell.")
        print("Type '/h' for help.")

    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        cli.save_history()

if __name__ == "__main__":
    main()