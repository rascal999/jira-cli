from jira import JIRAError
from urllib.parse import quote

def search_issues(self, query):
    try:
        issues = self.jira.search_issues(query)
        
        # Generate the JQL query URL
        base_url = self.jira.client_info()
        encoded_query = quote(query)
        jql_url = f"{base_url}/issues/?jql={encoded_query}"
        
        if issues:
            self.display_issues_table(issues, f"Search Results for '{query}'")
            self.console.print(f"\nJQL Query URL: {jql_url}", style="cyan")
        else:
            self.console.print("No issues found matching the query.", style="yellow")
        
        return issues, jql_url if issues else None
    
    except JIRAError as e:
        if e.status_code:
            self.console.print(f"Error searching for issues: HTTP {e.status_code} - {e.text}", style="red")
        else:
            self.console.print(f"Error searching for issues: {str(e)}", style="red")
        return [], None
    
    except Exception as e:
        self.console.print(f"Unexpected error searching for issues: {str(e)}", style="red")
        return [], None

def get_user_epics(self):
    try:
        current_user = self.jira.current_user()
        jql_query = f'reporter = {current_user} AND issuetype = Epic ORDER BY created DESC'
        epics = self.jira.search_issues(jql_query, maxResults=50, fields='summary,status,issuetype,assignee')
        if epics:
            self.display_issues_table(epics, "User Epics")
        else:
            self.console.print("You have no epics.", style="yellow")
    except JIRAError as e:
        self.console.print(f"An error occurred while fetching user epics: {str(e)}", style="red")

def get_recent_issues(self):
    try:
        jql = 'reporter = currentUser() ORDER BY updated DESC'
        issues = self.jira.search_issues(jql, maxResults=10)
        
        if issues:
            self.display_issues_table(issues, "Recently Updated Issues")
        else:
            self.console.print("No recent issues found.", style="yellow")
    except Exception as e:
        self.console.print(f"Error fetching recent issues: {str(e)}", style="red")
