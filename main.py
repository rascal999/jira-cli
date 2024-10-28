#!/usr/bin/env python3

import os
import importlib
import inspect
import readline
import atexit
import shlex
import glob
from rich.console import Console
from common.jira_client import get_jira_client
from common.jql_filters import load_jql_filters
import platform

CURRENT_TICKET_FILE = os.path.join('./cache/current_ticket.txt')

class InteractiveShell:
    def __init__(self):
        self.modules = {}
        self.aliases = {}
        self.load_modules()
        self.history_file = os.path.expanduser('~/.interactive_shell_history')
        self.current_ticket = self.load_current_ticket()
        if self.current_ticket:
            self.fetch_ticket_summary(self.current_ticket)
        else:
            self.current_ticket_summary = None
        self.last_displayed_tickets = []
        self.history_limit = 30
        self.setup_history()  # Move this after loading modules

    def load_modules(self):
        modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
        for filename in os.listdir(modules_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'modules.{module_name}')
                    self.modules[module_name] = module
                    if hasattr(module, 'ALIASES'):
                        for alias in module.ALIASES:
                            self.aliases[alias] = module_name
                except ImportError as e:
                    print(f"Error loading module {module_name}: {e}")

    def setup_history(self):
        # Set up readline with proper configuration first
        if platform.system() != 'Windows':
            readline.parse_and_bind('tab: complete')  # Use simple tab completion for all systems
        else:
            readline.parse_and_bind('tab: complete')
        
        # Remove any special key bindings that might interfere
        readline.set_completer_delims(' \t\n')
        readline.set_completer(self.complete)
        
        # Set up history
        readline.set_history_length(1000)
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        atexit.register(self.save_history)

    def save_history(self):
        readline.write_history_file(self.history_file)

    def display_current_ticket(self):
        if self.current_ticket:
            summary = f" - {self.current_ticket_summary}" if self.current_ticket_summary else ""
            return f"[{self.current_ticket}{summary}]"
        return ""

    def save_current_ticket(self):
        os.makedirs('./cache', exist_ok=True)
        with open(CURRENT_TICKET_FILE, 'w') as f:
            f.write(self.current_ticket or '')

    def load_current_ticket(self):
        if os.path.exists(CURRENT_TICKET_FILE):
            with open(CURRENT_TICKET_FILE, 'r') as f:
                ticket = f.read().strip() or None
            if ticket:
                self.fetch_ticket_summary(ticket)
            return ticket
        return None

    def fetch_ticket_summary(self, ticket):
        try:
            jira = get_jira_client()
            issue = jira.issue(ticket)
            self.current_ticket_summary = issue.fields.summary
        except Exception as e:
            print(f"Error fetching ticket summary: {str(e)}")
            self.current_ticket_summary = None

    def set_current_ticket(self, ticket):
        self.current_ticket = ticket
        self.current_ticket_summary = None
        if ticket:
            try:
                jira = get_jira_client()
                issue = jira.issue(ticket)
                self.current_ticket_summary = issue.fields.summary
            except Exception as e:
                print(f"Error fetching ticket summary: {str(e)}")
        self.save_current_ticket()

    def get_commands(self):
        """Returns a list of all available commands including modules and aliases"""
        # Add debug logging
        commands = list(self.modules.keys()) + list(self.aliases.keys())
        sorted_commands = sorted(set(commands))
        return sorted_commands

    def complete(self, text, state):
        try:
            # Get the current input line and cursor position
            buffer = readline.get_line_buffer()
            
            # Use shlex to properly handle quoted strings
            try:
                # Split the input, preserving quotes
                line = shlex.split(buffer) if buffer else []
            except ValueError:
                # Handle incomplete quoted strings
                line = buffer.split()

            # If there's no command yet or just starting to type
            if not line or (len(line) == 1 and not buffer.endswith(' ')):
                if not text and not buffer:
                    # Show all commands when pressing tab on empty line
                    commands = self.get_commands()
                    if state < len(commands):
                        return commands[state] + ' '
                    return None
                
                # Filter commands based on partial input
                commands = self.get_commands()
                matches = [cmd + ' ' for cmd in commands if cmd.startswith(text.lower())]
                if state < len(matches):
                    return matches[state]
                return None

            # Get the command (first word)
            cmd = line[0].strip().lower()

            # If the command is an alias, get the actual command
            if cmd in self.aliases:
                cmd = self.aliases[cmd]

            # Command-specific completions
            if cmd == 'attach':
                completions = self.complete_file_path(text, buffer, readline.get_begidx(), readline.get_endidx())
                if completions and state < len(completions):
                    return completions[state]
            elif cmd in ['link', 'unlink', 'parent']:
                # For commands that expect ticket IDs, suggest from history
                if self.last_displayed_tickets:
                    matches = [t + ' ' for t in self.last_displayed_tickets if t.lower().startswith(text.lower())]
                    if state < len(matches):
                        return matches[state]
            elif cmd == 'status':
                # Get available status transitions for current ticket
                if self.current_ticket:
                    try:
                        jira = get_jira_client()
                        issue = jira.issue(self.current_ticket)
                        transitions = jira.transitions(issue)
                        status_names = [t['name'].lower() for t in transitions]
                        matches = [s + ' ' for s in status_names if s.startswith(text.lower())]
                        if state < len(matches):
                            return matches[state]
                    except:
                        pass

            # Default completion: include commands, aliases, and ticket IDs
            all_completions = (self.get_commands() + 
                              list(self.aliases.keys()) + 
                              self.last_displayed_tickets)
            
            matches = [item for item in all_completions if item.lower().startswith(text.lower())]
            results = [m + ' ' for m in matches] + [None]
            return results[state]

        except Exception as e:
            print(f"Error completing command: {str(e)}")
            return None

    def complete_file_path(self, text, line, begidx, endidx):
        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return []  # arg not found

        fixed = line[before_arg+1:begidx]  # fixed portion of the arg
        arg = line[before_arg+1:endidx]
        pattern = arg + '*'

        completions = []
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                completions.append(path + os.path.sep)
            else:
                completions.append(path)

        return [c[len(fixed):] for c in completions]

    def run(self):
        console = Console()
        console.print("[bold cyan]Welcome to the jira-cli Interactive Shell![/bold cyan]")
        
        if self.current_ticket:
            console.print(f"[bold green]Current ticket: {self.current_ticket}[/bold green]")
        else:
            console.print("[yellow]No current ticket set.[/yellow]")
        
        self.execute_command('help')
        
        while True:
            try:
                current_ticket_display = self.display_current_ticket()
                user_input = input(f"{current_ticket_display}>>> ").strip()
                
                if not user_input:
                    if self.current_ticket:
                        self.execute_command('vid', [self.current_ticket])
                    else:
                        self.execute_command('help')
                    continue
                
                try:
                    # Use shlex to properly split the input, respecting quoted strings
                    command_parts = shlex.split(user_input)
                    command = command_parts[0].lower()
                    args = command_parts[1:]

                    self.execute_command(command, args)
                except ValueError as e:
                    if str(e) == "No closing quotation":
                        console.print("[bold red]Error:[/bold red] Your input contains an unclosed quotation. Please make sure all quotes are properly closed.")
                    else:
                        console.print(f"[bold red]Error:[/bold red] {str(e)}")
            except EOFError:
                print("\nExiting...")
                break
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                continue

    def execute_command(self, command, args=[]):
        # Check if the command looks like a TICKET-ID (e.g., PROJ-123)
        if '-' in command and not args:
            # Assume it's a TICKET-ID and pass it to the vid module
            module = self.modules['vid']
            if hasattr(module, 'run'):
                try:
                    run_func = module.run
                    if callable(run_func):
                        result = run_func([command], self.current_ticket)
                        if result:
                            self.set_current_ticket(result)
                    else:
                        print(f"The 'run' attribute of the 'vid' module is not callable.")
                except Exception as e:
                    print(f"Error executing command 'vid': {str(e)}")
                return

        # Check if the command is an alias
        if command in self.aliases:
            command = self.aliases[command]

        if command in self.modules:
            module = self.modules[command]
            if hasattr(module, 'run'):
                try:
                    run_func = module.run
                    if callable(run_func):
                        if len(inspect.signature(run_func).parameters) > 1:
                            result = run_func(args, self.current_ticket)
                        else:
                            result = run_func(args)
                        
                        # Update ticket ID history if the result is a list of ticket IDs
                        if isinstance(result, list) and all(isinstance(item, str) for item in result):
                            self.update_ticket_id_history(result)

                        if command == 'vid' and result:
                            self.set_current_ticket(result)
                        elif command == 'new' and result:
                            self.set_current_ticket(result)
                        elif command == 'delete' and result == "DELETED":
                            self.set_current_ticket(None)
                        elif command == 'parent' and result:
                            self.set_current_ticket(result)
                        elif command in ['clear', 'unfocus'] and result == "CLEARED":
                            self.set_current_ticket(None)
                        elif command == 'cp' and result:
                            self.set_current_ticket(result)
                    else:
                        print(f"The 'run' attribute of the '{command}' module is not callable.")
                except Exception as e:
                    print(f"Error executing command '{command}': {str(e)}")
            else:
                print(f"The '{command}' module does not have a 'run' function.")
        else:
            # If the command is unknown, perform a JQL search
            jql_query = f'summary ~ "{command} {" ".join(args)}"'
            jql_module = self.modules['jql']
            if hasattr(jql_module, 'run'):
                try:
                    run_func = jql_module.run
                    if callable(run_func):
                        result = run_func([jql_query], self.current_ticket)
                        if isinstance(result, list) and all(isinstance(item, str) for item in result):
                            self.update_ticket_id_history(result)
                    else:
                        print(f"The 'run' attribute of the 'jql' module is not callable.")
                except Exception as e:
                    print(f"Error executing JQL search: {str(e)}")
            else:
                print(f"The 'jql' module does not have a 'run' function.")

    def update_ticket_id_history(self, ticket_ids):
        """
        Update the history of displayed ticket IDs.
        """
        self.last_displayed_tickets = (self.last_displayed_tickets + ticket_ids)[-self.history_limit:]

shell = InteractiveShell()

if __name__ == "__main__":
    shell.run()
