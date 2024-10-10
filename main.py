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
from dotenv import load_dotenv
import importlib
import re

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

        # Initialize help_dict
        self.help_dict = {}

        # Dynamically load commands
        self.load_commands()

        # Initialize OpenAI client
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not specified
        if hasattr(openai, 'OpenAI'):
            # New version of OpenAI library
            self.openai_client = openai.OpenAI()
        else:
            # Old version of OpenAI library
            self.openai_client = openai

    def load_commands(self):
        commands_dir = os.path.join(os.path.dirname(__file__), 'commands')
        for filename in os.listdir(commands_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                module = importlib.import_module(f'commands.{module_name}')
                if hasattr(module, 'COMMAND') and hasattr(module, 'execute') and hasattr(module, 'HELP'):
                    command = getattr(module, 'COMMAND')
                    setattr(self, f'do_{command}', lambda arg, cmd=module.execute, self=self: cmd(self, arg))
                    self.help_dict[command] = getattr(module, 'HELP')

    def load_history(self):
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)

    def save_history(self):
        readline.write_history_file(self.history_file)

    def update_prompt(self):
        if self.current_ticket:
            issue = self.issue_manager.fetch_issue(self.current_ticket)
            if issue:
                if isinstance(issue, dict):
                    # Handle dictionary representation
                    key = issue['key']
                    summary = issue['fields']['summary']
                else:
                    # Handle object representation
                    key = issue.key
                    summary = issue.fields.summary
                self.prompt = f"{key} | {summary} > "
            else:
                self.prompt = "Jira CLI > "
        else:
            self.prompt = "Jira CLI > "

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

    def default(self, line):
        if re.match(r'^[A-Z]+-\d+$', line):
            self.do_view(line)
        else:
            self.console.print(f"Unknown command: {line}", style="red")

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
                'as': 'assign'
            }
            
            # Use the full command if available, otherwise keep the original
            command = command_map.get(command, command)
            
            return f"{command} {arg}".strip()
        return line

    def clear_screen(self):
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def set_current_ticket(self, ticket_key):
        self.current_ticket = ticket_key
        self.issue_manager.current_ticket = ticket_key  # If you want to keep this in sync
        self.prompt = f"{ticket_key} | {self.get_issue_summary(ticket_key)} > "

    def get_issue_summary(self, ticket_key):
        # Implement this to fetch and return the issue summary
        pass

    def onecmd(self, line):
        if re.match(r'^[A-Z]+-\d+$', line):
            self.default(line)
            return False  # Prevent cmd.Cmd from trying to find a do_* method
        return super().onecmd(line)

def main():
    load_dotenv()  # This line should be at the beginning of the main function
    if os.getenv('DEBUG', '0') == '1':
        print("Debug mode enabled. Logging Jira requests and responses.")
    
    parser = argparse.ArgumentParser(description="Jira CLI Tool")
    parser.add_argument("ticket", nargs="?", help="Jira ticket key (e.g., EXAMPLE-123)")
    args = parser.parse_args()

    jira_client = get_jira_client()
    console = Console()  # Create a Console object
    issue_manager = IssueManager(jira_client, console)  # Pass both jira_client and console
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