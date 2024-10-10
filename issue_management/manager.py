import re
import hashlib  # Add this import
from rich.console import Console
from .cache_manager import CacheManager
from .display import display_issue, display_comments, display_issues_table
from .search import search_issues, get_recent_issues
from .update import update_issue_description, update_issue_summary, link_issues, get_parent_issue
from .utils import get_color_for_user, get_status_style, get_available_statuses, format_date, resolve_user_mention, fetch_issue  # Add this import
from .delete import delete_issue
from commands.new import create_new_ticket  # Update this import
#from commands.epics import get_user_epics  # Add this import at the top of the file
import importlib
import os
from rich.text import Text
from jira import JIRAError  # Add this import
import io

class IssueManager:
    def __init__(self, jira_client):
        self.jira = jira_client
        self.console = Console()
        self.current_ticket = None
        self.user_cache = {}
        self.project_colors = {}
        self.user_colors = {}
        self.color_palette = [
            "cyan", "magenta", "green", "yellow", "blue", 
            "red", "purple", "bright_cyan", "bright_magenta", "bright_green",
            "bright_yellow", "bright_blue", "bright_red", "bright_black", "bright_white"
        ]
        self.status_colors = {
            "Backlog": "blue",
            "In Progress": "yellow",
            "Respond": "magenta",
            "OPEN": "green",
        }
        self.commands = self._load_commands()
        self.cache_manager = CacheManager()

    def _load_commands(self):
        commands = {}
        commands_dir = os.path.join(os.path.dirname(__file__), '..', 'commands')
        for filename in os.listdir(commands_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py extension
                module = importlib.import_module(f'commands.{module_name}')
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and not attr_name.startswith('_'):
                        commands[attr_name] = attr
        return commands

    def __getattr__(self, name):
        if name in self.commands:
            def wrapper(*args, **kwargs):
                return self.commands[name](self, *args, **kwargs)
            return wrapper
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def display_issue(self, issue):
        display_issue(self, issue)

    def display_comments(self, issue_key):
        display_comments(self, issue_key)

    def display_issues_table(self, issues, title):
        display_issues_table(self, issues, title)

    #def search_issues(self, query):
    #    return search_issues(self, query)

    #def get_user_epics(self):
    #    return get_user_epics(self)  # Change this line

    #def get_recent_issues(self):
    #    get_recent_issues(self)

    #def create_new_issue(self, parent=None):
    #    return create_new_ticket(self, parent)  # Update this line

    #def update_issue_description(self, issue_key):
    #    return update_issue_description(self, issue_key)

    def update_issue_summary(self, issue_key, new_summary):
        return update_issue_summary(self, issue_key, new_summary)

    #def delete_issue(self, issue_key):
    #    from .delete import delete_issue as delete_issue_func
    #    return delete_issue_func(self.jira, self.console, issue_key)

    def get_status_style(self, status):
        return get_status_style(status)

    def get_available_statuses(self, issue_key):
        try:
            transitions = self.jira.transitions(issue_key)
            return [t['name'] for t in transitions]
        except JIRAError as e:
            self.console.print(f"Error fetching available statuses for {issue_key}: {str(e)}", style="red")
            return []

    def fetch_issue(self, issue_key):
        cached_issue = self.cache_manager.get_issue(issue_key)
        if cached_issue:
            return cached_issue

        try:
            issue = self.jira.issue(issue_key, fields='summary,status,issuetype,priority,assignee,reporter,created,updated,description,comment')
            # Fetch all comments
            comments = self.jira.comments(issue)
            # Add comments to the issue object
            setattr(issue.fields, 'comment', comments)
            self.cache_manager.save_issue(issue)
            return issue
        except JIRAError as e:
            self.console.print(f"Error fetching issue {issue_key}: {str(e)}", style="red")
            return None

    def get_project_color(self, project_key):
        if project_key not in self.project_colors:
            # Generate a color based on the project key
            color_index = int(hashlib.md5(project_key.encode()).hexdigest(), 16) % len(self.color_palette)
            self.project_colors[project_key] = self.color_palette[color_index]
        return self.project_colors[project_key]

    def resolve_user_mention(self, account_id):
        try:
            user = self.jira.user(account_id)
            display_name = user.displayName
            return (display_name, self.get_color_for_user(display_name))
        except:
            return (account_id, "white")

    def add_comment(self, issue_key, comment_body):
        try:
            issue = self.jira.issue(issue_key)
            comment = self.jira.add_comment(issue, comment_body)
            self.console.print(f"Comment added successfully to {issue_key}", style="green")
            return comment
        except JIRAError as e:
            self.console.print(f"Error adding comment to {issue_key}: {str(e)}", style="red")
            return None

    def get_color_for_user(self, username):
        if username not in self.user_colors:
            color_index = len(self.user_colors) % len(self.color_palette)
            self.user_colors[username] = self.color_palette[color_index]
        return self.user_colors[username]

    def format_comment_body(self, body):
        mention_pattern = r'\[~accountid:([^\]]+)\]'
        
        formatted_text = Text()
        last_end = 0
        
        for match in re.finditer(mention_pattern, body):
            formatted_text.append(body[last_end:match.start()])
            
            account_id = match.group(1)
            display_name, color = self.resolve_user_mention(account_id)
            formatted_text.append(f"@{display_name}", style=color)
            
            last_end = match.end()
        
        formatted_text.append(body[last_end:])
        
        return formatted_text

    def get_subtasks(self, issue_key):
        try:
            issue = self.jira.issue(issue_key)
            subtasks = issue.fields.subtasks
            return subtasks
        except Exception as e:
            self.console.print(f"Error fetching subtasks for {issue_key}: {str(e)}", style="red")
            return []

    def fetch_issue(self, issue_key):
        return fetch_issue(self, issue_key)

    def get_epic_children(self, epic_key):
        try:
            jql = f'"Epic Link" = {epic_key}'
            return self.jira.search_issues(jql)
        except Exception as e:
            self.console.print(f"Error fetching epic children: {str(e)}", style="red")
            return []

    def add_attachment(self, issue_key, filename, content):
        try:
            issue = self.jira.issue(issue_key)
            attachment = io.StringIO(content)
            self.jira.add_attachment(issue=issue, attachment=attachment, filename=filename)
            return True
        except JIRAError as e:
            if e.status_code == 404:
                raise ValueError(f"Ticket {issue_key} not found.")
            elif e.status_code == 403:
                raise ValueError(f"You don't have permission to add attachments to ticket {issue_key}.")
            else:
                raise ValueError(f"Unable to save transcript to ticket {issue_key}.")
        except Exception as e:
            raise ValueError(f"Unexpected error: Unable to save transcript to ticket {issue_key}.")

    def get_color_for_author(self, author):
        return self.get_color_for_user(author)

    # ... other methods ...