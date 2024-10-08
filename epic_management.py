from rich.console import Console
from .utils import resolve_user_display_name
import os

console = Console()

class EpicManager:
    def __init__(self, jira_client):
        self.jira = jira_client
        self.epic_link_field = os.getenv('EPIC_LINK_FIELD_ID')
        self.epic_name_field = os.getenv('EPIC_NAME_FIELD_ID')

    def create_epic(self, project_key, summary, description):
        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': 'Epic'},
            self.epic_name_field: summary
        }
        new_epic = self.jira.create_issue(fields=issue_dict)
        console.print(f"[green]Epic {new_epic.key} created successfully[/green]")

    def list_user_epics(self, username):
        jql = f"issuetype=Epic AND reporter={username}"
        issues = self.jira.search_issues(jql)
        for issue in issues:
            console.print(f"{issue.key}: {issue.fields.summary}")

    def show_epic_children(self, epic_key):
        jql = f'"Epic Link" = {epic_key}'
        issues = self.jira.search_issues(jql)
        for issue in issues:
            console.print(f"{issue.key}: {issue.fields.summary}")
