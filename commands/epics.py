from rich.console import Console

console = Console()

def get_user_epics(issue_manager):
    try:
        current_user = issue_manager.jira.current_user()
        jql_query = f'reporter = {current_user} AND issuetype = Epic ORDER BY created DESC'
        epics = issue_manager.jira.search_issues(jql_query, maxResults=50, fields='summary,status,issuetype,assignee')
        if epics:
            issue_manager.display_issues_table(epics, "User Epics")
        else:
            console.print("You have no epics.", style="yellow")
        return epics
    except Exception as e:
        console.print(f"An error occurred while fetching user epics: {str(e)}", style="red")
        return []

def execute(cli, arg):
    get_user_epics(cli.issue_manager)

COMMAND = "epics"
HELP = "List all epics reported by you."