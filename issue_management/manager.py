from rich.console import Console
from .display import display_issue, display_comments, display_issues_table
from .search import search_issues, get_user_epics, get_recent_issues
from .create import create_new_issue
from .update import update_issue_description, update_issue_summary, link_issues
from .delete import delete_issue as delete_issue_func
from .utils import get_color_for_user, get_status_style, get_available_statuses
from jira import JIRAError
import re
import hashlib
from rich.text import Text
import os
import tempfile
import subprocess
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

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

    def display_issue(self, issue):
        display_issue(self, issue)

    def display_comments(self, issue_key):
        display_comments(self, issue_key)

    def display_issues_table(self, issues, title):
        display_issues_table(self, issues, title)

    def search_issues(self, query):
        return search_issues(self, query)

    def get_user_epics(self):
        get_user_epics(self)

    def get_recent_issues(self):
        get_recent_issues(self)

    def create_new_issue(self, parent=None):
        return create_new_issue(self, parent)

    def update_issue_description(self, issue_key):
        return update_issue_description(self, issue_key)

    def update_issue_summary(self, issue_key, new_summary):
        return update_issue_summary(self, issue_key, new_summary)

    def link_issues(self, from_issue, to_issue):
        return link_issues(self, from_issue, to_issue)

    def delete_issue(self, issue_key):
        from .delete import delete_issue as delete_issue_func
        return delete_issue_func(self.jira, self.console, issue_key)

    def get_color_for_user(self, username):
        return get_color_for_user(username)

    def get_status_style(self, status):
        return get_status_style(status)

    def get_available_statuses(self, issue_key):
        return get_available_statuses(self, issue_key)

    def fetch_issue(self, issue_key):
        if not re.match(r'^[A-Z]+-\d+$', issue_key):
            self.console.print(f"Invalid issue key format: {issue_key}", style="red")
            return None

        try:
            return self.jira.issue(issue_key)
        except JIRAError as e:
            if e.status_code == 404:
                self.console.print(f"Issue {issue_key} not found", style="yellow")
                return None
            else:
                self.console.print(f"Error fetching issue {issue_key}: {str(e)}", style="red")
                return None

    def get_project_color(self, project_key):
        if project_key not in self.project_colors:
            # Generate a color based on the project key
            color_index = int(hashlib.md5(project_key.encode()).hexdigest(), 16) % len(self.color_palette)
            self.project_colors[project_key] = self.color_palette[color_index]
        return self.project_colors[project_key]

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

    def resolve_user_mention(self, account_id):
        try:
            user = self.jira.user(account_id)
            display_name = user.displayName
            return (display_name, self.get_color_for_user(display_name))
        except:
            return (account_id, "white")

    def get_color_for_user(self, username):
        # If you don't have this method, you can implement it like this:
        color_hash = hashlib.md5(username.encode()).hexdigest()
        return f"#{color_hash[:6]}"

    def add_comment(self, issue_key, comment_body):
        try:
            issue = self.jira.issue(issue_key)
            comment = self.jira.add_comment(issue, comment_body)
            self.console.print(f"Comment added successfully to {issue_key}", style="green")
            return comment
        except JIRAError as e:
            self.console.print(f"Error adding comment to {issue_key}: {str(e)}", style="red")
            return None
