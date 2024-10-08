from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from issue_management import IssueManager
from search import SearchManager
from epic_management import EpicManager
from ai_integration import AIIntegration
from state import StateManager
from utils import validate_issue_key
from rich.console import Console

console = Console()

class InteractiveShell:
    def __init__(self, jira_client):
        self.issue_manager = IssueManager(jira_client)
        self.search_manager = SearchManager(jira_client)
        self.epic_manager = EpicManager(jira_client)
        self.ai_integration = AIIntegration()
        self.state_manager = StateManager()
        self.session = PromptSession()
        self.commands = {
            '/h': self.show_help,
            '/q': self.quit_shell,
            '/c': self.add_comment,
            # Add other command mappings here
        }

    def show_help(self):
        console.print("""
[bold]/h[/bold] - Show help
[bold]/q[/bold] - Quit
[bold]/c[/bold] - Add comment to the last viewed issue
[bold]/s[/bold] - Search issues
[bold]/v[/bold] - View issue details
[bold]/u[/bold] - Update issue status
[bold]/ai[/bold] - Ask AI a question
""")

    def quit_shell(self):
        console.print("[bold]Exiting...[/bold]")
        exit()

    def add_comment(self):
        last_issue = self.state_manager.get_last_viewed_issue()
        if not last_issue:
            console.print("[red]No issue in context.[/red]")
            return
        comment_body = self.session.prompt("Enter comment: ")
        self.issue_manager.add_comment(last_issue.key, comment_body)

    def start(self):
        console.print("[bold green]Welcome to Jira CLI! Type /h for help.[/bold green]")
        while True:
            try:
                user_input = self.session.prompt("> ")
                if user_input.startswith('/'):
                    cmd = user_input.strip()
                    if cmd in self.commands:
                        self.commands[cmd]()
                    else:
                        console.print(f"[red]Unknown command: {cmd}[/red]")
                else:
                    # Process as issue key or query
                    if validate_issue_key(user_input):
                        issue = self.issue_manager.fetch_issue(user_input)
                        if issue:
                            self.issue_manager.display_issue(issue)
                            self.state_manager.set_last_viewed_issue(issue)
                    else:
                        # Treat as a search query or AI question
                        self.process_query(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                self.quit_shell()

    def process_query(self, query):
        # Check if it's a JQL query
        if query.lower().startswith('jql:'):
            jql = query[4:].strip()
            issues = self.search_manager.search_issues(jql)
            self.search_manager.display_search_results(issues)
        else:
            # Assume it's an AI question
            response = self.ai_integration.ask_question(query)
            console.print(f"[blue]{response}[/blue]")
