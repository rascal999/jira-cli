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
from commands import clear, grab_url, delete, help, quit, comment, search, recent, tree, new, link, epics, update, parent, ai, rename, open_browser  # Add this import at the top of the file
from dotenv import load_dotenv

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

        # Initialize OpenAI client
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not specified
        if hasattr(openai, 'OpenAI'):
            # New version of OpenAI library
            self.openai_client = openai.OpenAI()
        else:
            # Old version of OpenAI library
            self.openai_client = openai

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

    def do_help(self, arg):
        """Show help message."""
        help.show_help()

    def do_quit(self, arg):
        """Quit the program."""
        return quit.quit_program()

    def do_comment(self, arg):
        """Add a comment to the current ticket."""
        comment.add_comment(self.issue_manager, self.current_ticket, arg)

    def do_recent(self, arg):
        """Show recently updated issues."""
        self.issue_manager.get_recent_issues()

    def do_search(self, arg):
        """Search for issues using JQL."""
        search.search_issues(self.issue_manager, arg)

    def do_delete(self, arg):
        """Delete a ticket."""
        if delete.delete_issue(self.issue_manager, self.current_ticket, arg):
            self.current_ticket = None
            self.update_prompt()
            self.console.print("Unfocused deleted ticket.", style="green")

    def do_tree(self, arg):
        """Display issue tree starting from current or specified ticket."""
        tree.display_issue_tree(self.issue_manager, self.current_ticket, arg)

    def do_new(self, arg):
        """Create a new ticket under the current ticket (epic or task), or create a new epic if no ticket is focused."""
        parent = self.current_ticket
        new_issue = new.create_new_ticket(self.issue_manager, parent)
        if new_issue:
            self.current_ticket = new_issue.key
            self.update_prompt(new_issue)

    def do_link(self, arg):
        """Link current ticket to specified ticket or unlink if already linked."""
        link.link_issues(self.issue_manager, self.current_ticket, arg)

    def do_epics(self, arg):
        """List all epics reported by you."""
        epics.list_user_epics(self.issue_manager)

    def do_clear(self, arg):
        """Clear the current focused ticket."""
        clear.clear_focus(self)

    def do_update(self, arg):
        """Update the description of the current ticket."""
        if not self.current_ticket:
            self.console.print("No ticket currently selected. Use /view <issue_key> to select a ticket.", style="yellow")
            return

        update.update_description(self.issue_manager, self.current_ticket)
        
        # Fetch the updated ticket
        updated_issue = self.issue_manager.fetch_issue(self.current_ticket)
        
        if updated_issue:
            # Display the updated issue
            self.issue_manager.display_issue(updated_issue)
            
            # Update the prompt with the latest information
            self.update_prompt(updated_issue)
        else:
            self.console.print(f"Failed to fetch updated ticket {self.current_ticket}", style="red")

    def do_parent(self, arg):
        """Change focus to parent ticket and display its details."""
        parent.focus_on_parent(self.issue_manager, self)

    def do_ai(self, arg):
        """Ask a question to ChatGPT."""
        ai.ask_ai(self.openai_client, arg)

    def do_rename(self, arg):
        """Rename the summary of the currently focused ticket."""
        rename.rename_issue(self.issue_manager, self.current_ticket, arg)

    def do_grab(self, arg):
        """Copy URL of current or specified issue to clipboard."""
        grab_url.grab_url(self.issue_manager, self.current_ticket, arg)

    def do_open(self, arg):
        """Open the current or specified ticket in the default web browser."""
        open_browser.open_in_browser(self.issue_manager, self.current_ticket, arg)

    def do_assign(self, arg):
        """Assign the current ticket or a specified ticket to the authenticated user."""
        from commands.assign import assign_issue
        assign_issue(self.issue_manager, self.current_ticket, arg)

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
        
        self.console.print()  # Add a newline at the end
        return stop

    def focus_on_issue(self, issue):
        self.current_ticket = issue.key
        self.update_prompt(issue)
        # Remove the display_issue call from here

    def emptyline(self):
        """Handle empty line input."""
        if self.prompt == "Jira> ":
            self.do_help(None)  # Changed from self.do_h(None) to self.do_help(None)
        elif self.current_ticket:
            issue = self.issue_manager.fetch_issue(self.current_ticket)
            if issue:
                self.issue_manager.display_issue(issue)
            else:
                self.console.print(f"Unable to fetch details for {self.current_ticket}", style="yellow")

    def precmd(self, line):
        """Preprocess the input line."""
        if line.startswith('/'):
            # Handle the case where only '/' is entered
            if line == '/':
                return 'help'  # Treat a single '/' as a request for help
            
            # Split the line into command and arguments
            parts = line[1:].split(maxsplit=1)
            if not parts:  # If parts is empty after splitting
                return 'help'  # Treat this as a request for help too
            
            command = parts[0]
            arg = parts[1] if len(parts) > 1 else ''
            
            # Map short commands to full commands
            command_map = {
                'h': 'help',
                'q': 'quit',
                'c': 'comment',
                'r': 'recent',
                's': 'search',
                'd': 'delete',
                't': 'tree',
                'n': 'new',
                'l': 'link',
                'e': 'epics',
                'x': 'clear',
                'u': 'update',
                'p': 'parent',
                'i': 'ai',
                'a': 'rename',
                'g': 'grab',
                'o': 'open',
                'as': 'assign'  # Add this line for the assign command
            }
            
            # Use the full command if available, otherwise keep the original
            command = command_map.get(command, command)
            
            return f"{command} {arg}".strip()
        return line

    def clear_screen(self):
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

def main():
    load_dotenv()  # This line should be at the beginning of the main function
    parser = argparse.ArgumentParser(description="Jira CLI Tool")
    parser.add_argument("ticket", nargs="?", help="Jira ticket key (e.g., EXAMPLE-123)")
    args = parser.parse_args()

    jira_client = get_jira_client()
    issue_manager = IssueManager(jira_client)
    cli = JiraCLI(issue_manager)

    # Show help message on startup
    cli.do_help(None)  # Changed from cli.do_h(None) to cli.do_help(None)

    if args.ticket:
        cli.onecmd(args.ticket)
    else:
        print("No initial ticket or search string provided. Starting interactive shell.")
        print("Type '/help' for help.")  # Updated to use '/help' instead of '/h'

    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        cli.save_history()

if __name__ == "__main__":
    main()
