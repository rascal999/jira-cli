#!/usr/bin/env python3

import requests
import sys
import os
import re
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from urllib.parse import quote
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
import tempfile
import subprocess
import openai  # Import the OpenAI library
from openai.api_resources.chat_completion import ChatCompletion  # Import ChatCompletion from api_resources

# Initialize rich console
console = Console()

# Maximum box width (default is 110 characters)
MAX_BOX_WIDTH = 110

# Define color schemes and styles for each issue section
STYLES = {
    'issue_details_header': 'bold blue',
    'issue_details_label': 'cyan',
    'issue_details_value': 'white',
    'comments_header': 'bold green',
    'comments_label': 'green',
    'comments_value': 'white',
    'subtasks_header': 'bold yellow',
    'subtasks_label': 'yellow',
    'subtasks_value': 'white',
    'linked_issues_header': 'bold magenta',
    'linked_issues_label': 'magenta',
    'linked_issues_value': 'white',
    'parent_issue_header': 'bold cyan',
    'parent_issue_label': 'cyan',
    'parent_issue_value': 'white',
    'epic_child_header': 'bold blue',
    'epic_child_label': 'blue',
    'epic_child_value': 'white',
    'error': 'red',
    'warning': 'yellow',
    'success': 'green',
    'search_result_header': 'green',
    'search_result_label': 'cyan',
    'search_result_value': 'white',
    'confirmation': 'bold red',
}

# Global variables
account_id_cache = {}  # Cache for account ID to display name mapping

def main():
    global epic_link_field_id, epic_name_field_id

    if len(sys.argv) > 3:
        console.print(f"[{STYLES['error']}]Usage: script.py [ISSUE_KEY_OR_SEARCH_STRING] [MAX_BOX_WIDTH][/]")
        sys.exit(1)

    input_arg = sys.argv[1] if len(sys.argv) >= 2 else None

    global MAX_BOX_WIDTH
    if len(sys.argv) == 3:
        try:
            MAX_BOX_WIDTH = int(sys.argv[2])
        except ValueError:
            console.print(f"[{STYLES['error']}]Invalid MAX_BOX_WIDTH value. It must be an integer.[/]")
            sys.exit(1)

    load_dotenv()

    jira_url = os.getenv('JIRA_URL')
    username = os.getenv('JIRA_USERNAME')
    api_token = os.getenv('JIRA_API_TOKEN')
    epic_link_field_id = os.getenv('EPIC_LINK_FIELD_ID')
    epic_name_field_id = os.getenv('EPIC_NAME_FIELD_ID')

    # Load OpenAI API key and model
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_model = os.getenv('OPENAI_MODEL', 'gpt-4')

    if not jira_url or not username or not api_token or not epic_link_field_id or not epic_name_field_id:
        console.print(f"[{STYLES['error']}]Please set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, EPIC_LINK_FIELD_ID, and EPIC_NAME_FIELD_ID in your .env file.[/]")
        sys.exit(1)

    if not openai_api_key:
        console.print(f"[{STYLES['error']}]Please set OPENAI_API_KEY in your .env file.[/]")
        sys.exit(1)

    openai.api_key = openai_api_key

    auth = (username, api_token)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    state = InteractiveShellState(jira_url, auth, headers, openai_model)

    if input_arg:
        process_input(input_arg, state, headers)
    else:
        console.print(f"[{STYLES['warning']}]No initial ticket or search string provided. Starting interactive shell.[/]")
    
    interactive_shell(state, headers)

class InteractiveShellState:
    def __init__(self, jira_url, auth, headers, openai_model):
        self.last_ticket_key = None
        self.jira_url = jira_url
        self.auth = auth
        self.headers = headers
        self.statuses_cache = {}
        self.session = PromptSession()
        self.openai_model = openai_model

    def get_completer(self):
        return StatusCompleter(self)

    def update_last_ticket_key(self, issue_key):
        self.last_ticket_key = issue_key
        self.statuses_cache.pop(issue_key, None)

class StatusCompleter(Completer):
    def __init__(self, state):
        self.state = state

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if self.state.last_ticket_key and not text.strip():
            issue_key = self.state.last_ticket_key
            if issue_key in self.state.statuses_cache:
                statuses = self.state.statuses_cache[issue_key]['statuses']
            else:
                transitions = get_transitions(issue_key, self.state.jira_url, self.state.auth, self.state.headers)
                statuses = [t['to']['name'] for t in transitions]
                self.state.statuses_cache[issue_key] = {'statuses': statuses, 'transitions': transitions}
            for status in statuses:
                yield Completion(status, start_position=0)

def interactive_shell(state, headers):
    console.print(f"\nType '/h' for help.")
    while True:
        try:
            if state.last_ticket_key:
                prompt_str = f"\n[{state.last_ticket_key}]> "
            else:
                prompt_str = "\n> "
            user_input = state.session.prompt(prompt_str, completer=state.get_completer()).strip()
        except KeyboardInterrupt:
            console.print(f"[{STYLES['warning']}]Interrupted. Use '/q' to exit.[/]")
            continue
        except EOFError:
            console.print(f"[{STYLES['success']}]Exiting...[/]")
            break

        if not user_input:
            if state.last_ticket_key:
                get_issue_details(state.last_ticket_key, state.jira_url, state.auth, headers)
            else:
                console.print(f"[{STYLES['warning']}]No ticket in focus to display details.[/]")
            continue

        if state.last_ticket_key:
            issue_key = state.last_ticket_key
            if issue_key in state.statuses_cache:
                statuses = state.statuses_cache[issue_key]['statuses']
            else:
                transitions = get_transitions(issue_key, state.jira_url, state.auth, headers)
                statuses = [t['to']['name'] for t in transitions]
                state.statuses_cache[issue_key] = {'statuses': statuses, 'transitions': transitions}
            if user_input in statuses:
                update_issue_status(issue_key, user_input, state, headers)
                continue

        if user_input.startswith('/'):
            if user_input == '/q':
                console.print(f"[{STYLES['success']}]Exiting...[/]")
                break
            elif user_input.startswith('/c'):
                if state.last_ticket_key:
                    comment = user_input[2:].strip()
                    if comment:
                        add_comment(state.last_ticket_key, state.jira_url, state.auth, headers, comment)
                    else:
                        console.print(f"[{STYLES['warning']}]Please provide a comment after '/c'.[/]")
                else:
                    console.print(f"[{STYLES['warning']}]No ticket selected to add a comment.[/]")
            elif user_input == '/h':
                display_help()
            elif user_input == '/s':
                console.print(f"[{STYLES['search_result_header']}]Enter your JQL query:[/]")
                jql_query = state.session.prompt("> ").strip()
                execute_jql(jql_query, state.jira_url, state.auth, headers)
            elif user_input.startswith('/d'):
                delete_command = user_input.split()
                if len(delete_command) == 2:
                    ticket_id = delete_command[1].strip()
                    delete_ticket(ticket_id, state.jira_url, state.auth, headers, state.session)
                else:
                    console.print(f"[{STYLES['warning']}]Usage: /d TICKET_ID[/]")
            elif user_input == '/r':
                display_recent_tickets(state.jira_url, state.auth, headers)
            elif user_input.startswith('/t'):
                tokens = user_input.split()
                if len(tokens) == 1:
                    if state.last_ticket_key:
                        print_issue_tree(state.last_ticket_key, state.jira_url, state.auth, headers)
                    else:
                        console.print(f"[{STYLES['warning']}]No ticket selected to display tree.[/]")
                elif len(tokens) == 2:
                    ticket_id = tokens[1].strip()
                    print_issue_tree(ticket_id, state.jira_url, state.auth, headers)
                else:
                    console.print(f"[{STYLES['warning']}]Usage: /t [TICKET_ID][/]")
            elif user_input.startswith('/n'):
                if state.last_ticket_key:
                    create_new_issue(state.last_ticket_key, state.jira_url, state.auth, headers, state.session, state)
                else:
                    create_new_epic(state.jira_url, state.auth, headers, state.session, state)
            elif user_input.startswith('/l'):
                tokens = user_input.split()
                if len(tokens) == 2:
                    if state.last_ticket_key:
                        target_ticket = tokens[1].strip()
                        link_issues(state.last_ticket_key, target_ticket, state.jira_url, state.auth, headers)
                    else:
                        console.print(f"[{STYLES['warning']}]No ticket in focus to link from.[/]")
                else:
                    console.print(f"[{STYLES['warning']}]Usage: /l TICKET_ID[/]")
            elif user_input == '/e':
                list_user_epics(state.jira_url, state.auth, headers)
            elif user_input == '/x':
                state.update_last_ticket_key(None)
                console.print(f"[{STYLES['success']}]Current focused ticket cleared.[/]")
            elif user_input == '/u':
                if state.last_ticket_key:
                    update_description(state.last_ticket_key, state.jira_url, state.auth, headers)
                else:
                    console.print(f"[{STYLES['warning']}]No ticket selected to update description.[/]")
            elif user_input == '/p':
                if state.last_ticket_key:
                    issue = get_issue(state.last_ticket_key, state.jira_url, state.auth, headers)
                    if issue:
                        parent = issue.get('fields', {}).get('parent')
                        if parent:
                            parent_key = parent.get('key')
                            state.update_last_ticket_key(parent_key)
                            get_issue_details(parent_key, state.jira_url, state.auth, headers)
                        else:
                            console.print(f"[{STYLES['warning']}]No parent issue found for {state.last_ticket_key}.[/]")
                    else:
                        console.print(f"[{STYLES['error']}]Failed to fetch issue {state.last_ticket_key}.[/]")
                else:
                    console.print(f"[{STYLES['warning']}]No ticket selected to display parent ticket.[/]")
            elif user_input.startswith('/i'):
                question = user_input[2:].strip()
                if question:
                    get_chatgpt_response(question, state)
                else:
                    console.print(f"[{STYLES['warning']}]Please provide a question after '/i'.[/]")
            else:
                console.print(f"[{STYLES['warning']}]Unknown command. Type '/h' for help.[/]")
        else:
            process_input(user_input, state, headers)

def get_chatgpt_response(question, state):
    try:
        response = ChatCompletion.create(
            model=state.openai_model,
            messages=[
                {"role": "user", "content": question}
            ]
        )
        answer = response['choices'][0]['message']['content']
        console.print(f"\n[{STYLES['search_result_header']}]ChatGPT Response:[/]\n{answer}")
    except Exception as e:
        console.print(f"[{STYLES['error']}]An error occurred while getting response from ChatGPT: {e}[/]")

def update_description(issue_key, jira_url, auth, headers):
    # Fetch the current description
    issue = get_issue(issue_key, jira_url, auth, headers)
    if not issue:
        console.print(f"[{STYLES['error']}]Failed to fetch issue {issue_key}.[/]")
        return
    fields = issue.get('fields', {})
    current_description = fields.get('description', '')
    # Create a temporary file with the current description
    editor = os.environ.get('EDITOR', 'vim')
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.tmp') as tmp_file:
            tmp_file_name = tmp_file.name
            tmp_file.write(current_description)
            tmp_file.flush()
        # Open the editor
        subprocess.call([editor, tmp_file_name])
        # Read the modified description
        with open(tmp_file_name, 'r') as tmp_file:
            new_description = tmp_file.read()
        # Update the issue's description
        url = f"{jira_url}/rest/api/2/issue/{issue_key}"
        payload = {
            "fields": {
                "description": new_description
            }
        }
        response = requests.put(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 204:
            console.print(f"[{STYLES['success']}]Description for {issue_key} updated successfully.[/]")
        else:
            console.print(f"[{STYLES['error']}]Failed to update description. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except Exception as e:
        console.print(f"[{STYLES['error']}]An error occurred while updating description: {e}[/]")
    finally:
        # Clean up the temporary file
        try:
            os.remove(tmp_file_name)
        except Exception:
            pass

def display_help():
    console.print(f"""
[{STYLES['search_result_header']}]Available Commands:[/]

/h          - Show this help message.
/q          - Quit the program.
/c          - Add a comment to the last ticket. Usage: /c Your comment here.
/s          - Enter JQL mode to execute a JQL query.
/d TICKET   - Delete a ticket. Usage: /d TICKET_ID
/r          - Display top 10 recently updated tickets reported by you.
/t [TICKET] - Display issue tree starting from current or specified ticket.
/n          - Create a new ticket under the current ticket (epic or task), or create a new epic if no ticket is focused.
/l TICKET   - Link current ticket to specified ticket as 'Relates to'.
/e          - List all epics reported by you.
/x          - Clear the current focused ticket.
/u          - Update the description of the currently focused ticket.
/p          - Change focus to parent ticket and display its details.
/i          - Ask a question to ChatGPT. Usage: /i Your question here.

Type a ticket ID or search string to display ticket information or search results.

When a ticket is focused, press [bold][Tab][/bold] on an empty prompt to cycle through possible statuses. Press [bold][Enter][/bold] to update the ticket to the selected status.
""")

def add_comment(issue_key, jira_url, auth, headers, comment):
    url = f"{jira_url}/rest/api/2/issue/{issue_key}/comment"
    payload = {
        "body": comment
    }
    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 201:
            console.print(f"[{STYLES['success']}]Comment added to {issue_key} successfully.[/]")
        else:
            console.print(f"[{STYLES['error']}]Failed to add comment. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while adding a comment: {e}[/]")

def delete_ticket(issue_key, jira_url, auth, headers, session):
    # Fetch ticket details first
    issue = get_issue(issue_key, jira_url, auth, headers)
    if not issue:
        return  # Error message already printed in get_issue()

    # Display issue details for confirmation
    print_issue_details(issue, jira_url, auth, headers)

    # Ask for confirmation
    console.print(f"[{STYLES['confirmation']}]Are you sure you want to delete {issue_key}? This action cannot be undone. (yes/no)[/]")
    confirmation = session.prompt("> ").strip().lower()
    if confirmation == 'yes':
        # Proceed to delete the ticket
        url = f"{jira_url}/rest/api/2/issue/{issue_key}"
        try:
            response = requests.delete(url, headers=headers, auth=auth)
            if response.status_code == 204:
                console.print(f"[{STYLES['success']}]Ticket {issue_key} deleted successfully.[/]")
            else:
                console.print(f"[{STYLES['error']}]Failed to delete ticket. Status code: {response.status_code}[/]")
                print("Response:", response.text)
        except requests.exceptions.RequestException as e:
            console.print(f"[{STYLES['error']}]An error occurred while deleting the ticket: {e}[/]")
    else:
        console.print(f"[{STYLES['warning']}]Deletion cancelled.[/]")

def execute_jql(jql_query, jira_url, auth, headers):
    params = {
        'jql': jql_query,
        'fields': 'key,summary,issuetype,status,assignee,reporter',  # Fields to retrieve
        'maxResults': 100  # Increased to return more results
    }

    search_url = f"{jira_url}/rest/api/2/search"

    try:
        # Make the GET request to search for issues
        response = requests.get(search_url, headers=headers, auth=auth, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            search_results = response.json()
            issues = search_results.get('issues', [])

            if issues:
                console.print(f"[{STYLES['search_result_header']}]Found {len(issues)} issue(s):[/]")
                for issue in issues:
                    print_issue_summary(issue)
            else:
                console.print(f"[{STYLES['warning']}]No issues found for the provided JQL query.[/]")
            
            # Display the URL for the JQL query
            jql_encoded = quote(jql_query)
            jql_url = f"{jira_url}/issues/?jql={jql_encoded}"
            console.print(f"\n[{STYLES['search_result_header']}]JQL Query URL:[/]\n{jql_url}")

        else:
            # Print an error message if the request was not successful
            console.print(f"[{STYLES['error']}]Failed to execute JQL query. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the request
        console.print(f"[{STYLES['error']}]An error occurred while executing JQL query: {e}[/]")

def display_recent_tickets(jira_url, auth, headers):
    # Construct JQL query to get top 10 most recently updated tickets reported by the user
    jql_query = 'reporter = currentUser() ORDER BY updated DESC'
    params = {
        'jql': jql_query,
        'fields': 'key,summary,issuetype,status,assignee,reporter',
        'maxResults': 10
    }
    search_url = f"{jira_url}/rest/api/2/search"
    try:
        response = requests.get(search_url, headers=headers, auth=auth, params=params)
        if response.status_code == 200:
            search_results = response.json()
            issues = search_results.get('issues', [])
            if issues:
                console.print(f"[{STYLES['search_result_header']}]Your Top 10 Recently Updated Tickets:[/]")
                for issue in issues:
                    print_issue_summary(issue)
            else:
                console.print(f"[{STYLES['warning']}]No recent tickets found reported by you.[/]")
        else:
            console.print(f"[{STYLES['error']}]Failed to retrieve recent tickets. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while retrieving recent tickets: {e}[/]")

def process_input(input_arg, state, headers):
    input_arg = input_arg.strip()
    if is_valid_issue_key(input_arg):
        # Input is a valid issue key, retrieve and print issue details
        issue_key = input_arg.upper()
        get_issue_details(issue_key, state.jira_url, state.auth, headers)
        state.update_last_ticket_key(issue_key)  # Update the last ticket key in state
    else:
        # Input is a search string, perform a search and print matching issues
        search_string = input_arg
        search_issues(search_string, state.jira_url, state.auth, headers)

def is_valid_issue_key(key):
    # Regular expression pattern for Jira issue keys (e.g., PROJ-123)
    pattern = r'^[A-Z][A-Z0-9]+-\d+$'
    return re.match(pattern, key.upper()) is not None

def get_issue_details(issue_key, jira_url, auth, headers):
    # Fetch issue details
    issue = get_issue(issue_key, jira_url, auth, headers)
    if issue:
        print_issue_details(issue, jira_url, auth, headers)
        print_issue_comments(issue_key, jira_url, auth, headers)  # Fetch and print comments

        # Check if the issue is an Epic
        if is_epic(issue):
            print_epic_children(issue_key, jira_url, auth, headers)
        else:
            print_subtasks(issue, jira_url, auth, headers)       # Print sub-tasks and their child tickets

        print_linked_issues(issue)  # Print linked issues if any
        print_parent_issue(issue)   # Print parent issue if applicable
    else:
        return  # Error message already printed in get_issue()

def is_epic(issue):
    # Check if the issue type is 'Epic'
    issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', '')
    return issue_type.lower() == 'epic'

def print_epic_children(epic_key, jira_url, auth, headers):
    # Fetch and print child issues of the epic
    issues = get_epic_children(epic_key, jira_url, auth, headers)
    if issues:
        console.print(f"\n[{STYLES['epic_child_header']}]Child Issues of Epic:[/]\n")
        for issue in issues:
            key = issue.get('key', 'N/A')
            fields = issue.get('fields', {})
            summary = fields.get('summary', 'N/A')
            status = fields.get('status', {}).get('name', 'N/A')
            issue_type = fields.get('issuetype', {}).get('name', 'N/A')
            assignee_field = fields.get('assignee')
            if assignee_field is not None:
                assignee = assignee_field.get('displayName', 'Unassigned')
            else:
                assignee = 'Unassigned'
            console.print(f"[{STYLES['epic_child_label']}] - {key}: [{STYLES['epic_child_value']}]{summary} [{status}] (Assignee: {assignee})[/]")
    else:
        pass  # Do not output any message if no child issues are found

def get_epic_children(epic_key, jira_url, auth, headers):
    # Construct JQL query to find all issues linked to the Epic
    jql = f'"Epic Link" = {epic_key} ORDER BY created ASC'

    params = {
        'jql': jql,
        'fields': 'key,summary,status,issuetype,assignee',
        'maxResults': 100  # Adjusted as needed
    }

    search_url = f"{jira_url}/rest/api/2/search"

    try:
        response = requests.get(search_url, headers=headers, auth=auth, params=params)

        if response.status_code == 200:
            search_results = response.json()
            issues = search_results.get('issues', [])
            return issues
        else:
            console.print(f"[{STYLES['error']}]Failed to fetch child issues for Epic {epic_key}. Status code: {response.status_code}[/]")
            print("Response:", response.text)
            return []
        return []
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while fetching child issues for Epic {epic_key}: {e}[/]")
        return []

def search_issues(search_string, jira_url, auth, headers):
    # Construct the JQL query to search for issues with summaries containing the search string
    jql = f'summary ~ "{search_string}" ORDER BY created DESC'

    # URL encode the JQL query
    params = {
        'jql': jql,
        'fields': 'key,summary,issuetype,status,assignee,reporter',  # Fields to retrieve
        'maxResults': 100  # Increased to return more results
    }

    search_url = f"{jira_url}/rest/api/2/search"

    try:
        # Make the GET request to search for issues
        response = requests.get(search_url, headers=headers, auth=auth, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            search_results = response.json()
            issues = search_results.get('issues', [])

            if issues:
                console.print(f"[{STYLES['search_result_header']}]Found {len(issues)} issue(s) matching '{search_string}':[/]")
                for issue in issues:
                    print_issue_summary(issue)
            else:
                console.print(f"[{STYLES['warning']}]No issues found matching '{search_string}'.[/]")
        else:
            # Print an error message if the request was not successful
            console.print(f"[{STYLES['error']}]Failed to search issues. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the request
        console.print(f"[{STYLES['error']}]An error occurred while searching issues: {e}[/]")

def resolve_account_ids(text, jira_url, auth, headers):
    if not text:
        return text

    pattern = r'\[~accountid:([a-zA-Z0-9:-]+)\]'
    account_ids = re.findall(pattern, text)
    unique_account_ids = set(account_ids)

    for account_id in unique_account_ids:
        if account_id in account_id_cache:
            display_name = account_id_cache[account_id]
        else:
            # Fetch user info from Jira API
            user_info = get_user_info(account_id, jira_url, auth, headers)
            if user_info:
                display_name = user_info.get('displayName', 'Unknown User')
                account_id_cache[account_id] = display_name
            else:
                display_name = 'Unknown User'

        # Replace all occurrences of the account ID with the display name
        text = re.sub(rf'\[~accountid:{re.escape(account_id)}\]', display_name, text)

    return text

def get_user_info(account_id, jira_url, auth, headers):
    url = f"{jira_url}/rest/api/2/user?accountId={quote(account_id)}"
    try:
        response = requests.get(url, headers=headers, auth=auth)
        if response.status_code == 200:
            return response.json()
        else:
            console.print(f"[{STYLES['warning']}]Failed to retrieve user info for account ID {account_id}. Status code: {response.status_code}[/]")
            return None
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while fetching user info: {e}[/]")
        return None

def print_issue_details(issue, jira_url, auth, headers):
    # Extract issue details with default values if keys are missing
    key = issue.get('key', 'N/A')  # The issue key
    fields = issue.get('fields', {})  # All the fields of the issue
    summary = fields.get('summary', 'N/A')  # The summary/title of the issue
    issue_type = fields.get('issuetype', {}).get('name', 'N/A')  # The type of issue (e.g., Bug)
    status = fields.get('status', {}).get('name', 'N/A')  # The current status of the issue

    # Handle the assignee field safely
    assignee_field = fields.get('assignee')
    if assignee_field is not None:
        assignee = assignee_field.get('displayName', 'Unassigned')
    else:
        assignee = 'Unassigned'

    # Handle the reporter field safely
    reporter_field = fields.get('reporter')
    if reporter_field is not None:
        reporter = reporter_field.get('displayName', 'Unknown')
    else:
        reporter = 'Unknown'

    description = fields.get('description', 'N/A')  # The description of the issue
    description = resolve_account_ids(description, jira_url, auth, headers)

    # Construct the issue URL
    issue_url = f"{jira_url}/browse/{key}"

    # Create a Text object for the issue details
    issue_text = Text()
    issue_text.append(f"Issue Key: ", style=STYLES['issue_details_label'])
    issue_text.append(f"{key}\n", style=STYLES['issue_details_value'])

    issue_text.append(f"Issue URL: ", style=STYLES['issue_details_label'])
    issue_text.append(f"{issue_url}\n", style=STYLES['issue_details_value'])

    issue_text.append(f"Summary: ", style=STYLES['issue_details_label'])
    issue_text.append(f"{summary}\n", style=STYLES['issue_details_value'])

    issue_text.append(f"Issue Type: ", style=STYLES['issue_details_label'])
    issue_text.append(f"{issue_type}\n", style=STYLES['issue_details_value'])

    issue_text.append(f"Status: ", style=STYLES['issue_details_label'])
    issue_text.append(f"{status}\n", style=STYLES['issue_details_value'])

    issue_text.append(f"Assignee: ", style=STYLES['issue_details_label'])
    issue_text.append(f"{assignee}\n", style=STYLES['issue_details_value'])

    issue_text.append(f"Reporter: ", style=STYLES['issue_details_label'])
    issue_text.append(f"{reporter}\n", style=STYLES['issue_details_value'])

    issue_text.append(f"Description:\n", style=STYLES['issue_details_label'])
    issue_text.append(f"{description}", style=STYLES['issue_details_value'])

    # Create a Panel around the issue details with configurable width
    issue_panel = Panel(
        issue_text,
        title="Issue Details",
        title_align="left",
        border_style=STYLES['issue_details_header'],
        box=box.ROUNDED,
        width=MAX_BOX_WIDTH
    )

    console.print(issue_panel)

def print_issue_comments(issue_key, jira_url, auth, headers):
    # Construct the URL to fetch comments for the issue
    comments_url = f"{jira_url}/rest/api/2/issue/{issue_key}/comment"

    try:
        # Make the GET request to fetch comments
        response = requests.get(comments_url, headers=headers, auth=auth)

        # Check if the request was successful
        if response.status_code == 200:
            comments_data = response.json()  # Parse the JSON response
            comments = comments_data.get('comments', [])  # Get the list of comments

            # Check if there are any comments
            if comments:
                console.print(f"\n[{STYLES['comments_header']}]Comments:[/]\n")
                # Iterate over each comment and print details
                for comment in comments:
                    author_field = comment.get('author')
                    if author_field is not None:
                        author = author_field.get('displayName', 'Unknown')
                    else:
                        author = 'Unknown'
                    created = comment.get('created', 'N/A')
                    body = comment.get('body', '')
                    body = resolve_account_ids(body, jira_url, auth, headers)

                    # Create a Text object for the comment
                    comment_text = Text()
                    comment_text.append(f"Author: ", style=STYLES['comments_label'])
                    comment_text.append(f"{author}\n", style=STYLES['comments_value'])

                    comment_text.append(f"Created: ", style=STYLES['comments_label'])
                    comment_text.append(f"{created}\n", style=STYLES['comments_value'])

                    comment_text.append(f"Comment:\n", style=STYLES['comments_label'])
                    comment_text.append(f"{body}", style=STYLES['comments_value'])

                    # Create a Panel around the comment with configurable width
                    comment_panel = Panel(
                        comment_text,
                        border_style=STYLES['comments_header'],
                        box=box.ROUNDED,
                        width=MAX_BOX_WIDTH
                    )
                    console.print(comment_panel)
            else:
                pass  # Do not output any message if no comments are found
        else:
            console.print(f"[{STYLES['error']}]Failed to retrieve comments for issue {issue_key}. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while fetching comments: {e}[/]")

def print_issue_summary(issue):
    # Extract basic issue details
    key = issue.get('key', 'N/A')
    fields = issue.get('fields', {})
    summary = fields.get('summary', 'N/A')
    issue_type = fields.get('issuetype', {}).get('name', 'N/A')
    status = fields.get('status', {}).get('name', 'N/A')
    status_category = fields.get('status', {}).get('statusCategory', {}).get('name', '')

    # Handle the assignee field safely
    assignee_field = fields.get('assignee')
    if assignee_field is not None:
        assignee = assignee_field.get('displayName', 'Unassigned')
    else:
        assignee = 'Unassigned'

    # Create a Text object for the summary
    summary_text = Text(summary, style=STYLES['search_result_value'])
    if status_category == 'Done':
        summary_text.stylize('strikethrough')

    # Print a summary line for the issue with colors
    console.print(f"[{STYLES['search_result_label']}]{key} [{status}]: ", end='')
    console.print(summary_text)
    console.print(f"[{STYLES['search_result_label']}]Type: {issue_type}, Assignee: {assignee}\n[/]")

def print_subtasks(issue, jira_url, auth, headers, level=0):
    fields = issue.get('fields', {})
    subtasks = fields.get('subtasks', [])

    indent = '    ' * level  # Indentation based on level

    if subtasks:
        if level == 0:
            console.print(f"\n[{STYLES['subtasks_header']}]Sub-tasks:[/]\n")
        for subtask in subtasks:
            subtask_key = subtask.get('key', 'N/A')
            subtask_summary = subtask.get('fields', {}).get('summary', 'N/A')
            subtask_status = subtask.get('fields', {}).get('status', {}).get('name', 'N/A')
            console.print(f"{indent}[{STYLES['subtasks_label']}] - {subtask_key}: [{STYLES['subtasks_value']}]{subtask_summary} [{subtask_status}][/]")
            # Fetch the full subtask issue data
            subtask_issue = get_issue(subtask_key, jira_url, auth, headers)
            if subtask_issue:
                # Recursively print sub-tasks of this subtask
                print_subtasks(subtask_issue, jira_url, auth, headers, level=level+1)
    else:
        pass  # Do not output any message if no subtasks are found

def get_issue(issue_key, jira_url, auth, headers):
    # Construct the API endpoint URL for the specific issue
    url = f"{jira_url}/rest/api/2/issue/{issue_key}"
    try:
        # Make the GET request to the Jira API
        response = requests.get(url, headers=headers, auth=auth)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            return response.json()  # Return the issue data
        else:
            console.print(f"[{STYLES['error']}]Issue {issue_key} not found. Status code: {response.status_code}[/]")
            return None
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while fetching issue {issue_key}: {e}[/]")
        return None

def print_linked_issues(issue):
    fields = issue.get('fields', {})
    issuelinks = fields.get('issuelinks', [])

    if issuelinks:
        console.print(f"\n[{STYLES['linked_issues_header']}]Linked Issues:[/]\n")
        for link in issuelinks:
            link_type = link.get('type', {}).get('name', 'Linked')
            outward_issue = link.get('outwardIssue')
            inward_issue = link.get('inwardIssue')

            if outward_issue:
                linked_issue_key = outward_issue.get('key', 'N/A')
                summary = outward_issue.get('fields', {}).get('summary', 'N/A')
                link_description = link.get('type', {}).get('outward', 'Related to')
                console.print(f"[{STYLES['linked_issues_label']}] - {link_description}: [{STYLES['linked_issues_value']}]{linked_issue_key} - {summary}[/]")
            elif inward_issue:
                linked_issue_key = inward_issue.get('key', 'N/A')
                summary = inward_issue.get('fields', {}).get('summary', 'N/A')
                link_description = link.get('type', {}).get('inward', 'Related from')
                console.print(f"[{STYLES['linked_issues_label']}] - {link_description}: [{STYLES['linked_issues_value']}]{linked_issue_key} - {summary}[/]")
            else:
                console.print(f"[{STYLES['linked_issues_label']}] - {link_type}: Unknown issue[/]")
    else:
        pass  # Do not output any message if no linked issues are found

def print_parent_issue(issue):
    fields = issue.get('fields', {})
    parent = fields.get('parent')

    if parent:
        parent_key = parent.get('key', 'N/A')
        parent_fields = parent.get('fields', {})
        parent_summary = parent_fields.get('summary', 'N/A')
        parent_status = parent_fields.get('status', {}).get('name', 'N/A')
        console.print(f"\n[{STYLES['parent_issue_header']}]Parent Issue:[/]")
        console.print(f"[{STYLES['parent_issue_label']}] - {parent_key}: [{STYLES['parent_issue_value']}]{parent_summary} [{parent_status}][/]")
    else:
        pass  # Do not output any message if no parent issue is found

def print_issue_tree(issue_key, jira_url, auth, headers, level=0):
    issue = get_issue(issue_key, jira_url, auth, headers)
    if not issue:
        return
    fields = issue.get('fields', {})
    summary = fields.get('summary', 'N/A')
    status = fields.get('status', {}).get('name', 'N/A')
    issue_type = fields.get('issuetype', {}).get('name', 'N/A')

    indent = '    ' * level
    console.print(f"{indent}[{STYLES['search_result_label']}]{issue_key}: [{STYLES['search_result_value']}]{summary} [{status}] (Type: {issue_type})[/]")

    if is_epic(issue):
        # Fetch epic's child issues
        child_issues = get_epic_children(issue_key, jira_url, auth, headers)
        if child_issues:
            for child_issue in child_issues:
                print_issue_tree(child_issue.get('key'), jira_url, auth, headers, level=level+1)
    else:
        # Print subtasks
        subtasks = fields.get('subtasks', [])
        for subtask in subtasks:
            subtask_key = subtask.get('key', 'N/A')
            print_issue_tree(subtask_key, jira_url, auth, headers, level=level+1)

def create_new_issue(issue_key, jira_url, auth, headers, session, state):
    issue = get_issue(issue_key, jira_url, auth, headers)
    if not issue:
        return

    fields = issue.get('fields', {})
    issue_type = fields.get('issuetype', {}).get('name', 'N/A').lower()

    if issue_type == 'sub-task':
        console.print(f"[{STYLES['warning']}]Cannot create a new issue under a sub-task.[/]")
        return

    # Ask for summary and description
    console.print(f"[{STYLES['search_result_header']}]Enter summary for the new issue:[/]")
    summary = session.prompt("> ").strip()
    console.print(f"[{STYLES['search_result_header']}]Enter description for the new issue:[/]")
    description = session.prompt("> ").strip()

    if not summary:
        console.print(f"[{STYLES['warning']}]Summary cannot be empty.[/]")
        return

    # Get project key from issue_key
    project_key = issue_key.split('-')[0]

    # Prepare payload
    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "summary": summary,
            "description": description
        }
    }

    if is_epic(issue):
        # Create a standard issue and link it to the epic
        # Need to specify the issue type, e.g., "Task" or "Story"
        console.print(f"[{STYLES['search_result_header']}]Enter issue type (e.g., Task, Story):[/]")
        issue_type_name = session.prompt("> ").strip()
        if not issue_type_name:
            console.print(f"[{STYLES['warning']}]Issue type cannot be empty.[/]")
            return

        payload["fields"]["issuetype"] = {"name": issue_type_name}
        payload["fields"][epic_link_field_id] = issue_key  # Link to epic
    else:
        # Create a sub-task under the current issue
        payload["fields"]["issuetype"] = {"name": "Sub-task"}
        payload["fields"]["parent"] = {"key": issue_key}

    # Send POST request to create issue
    url = f"{jira_url}/rest/api/2/issue"
    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 201:
            new_issue = response.json()
            new_issue_key = new_issue.get('key')
            console.print(f"[{STYLES['success']}]Issue {new_issue_key} created successfully.[/]")
            state.update_last_ticket_key(new_issue_key)
            get_issue_details(new_issue_key, jira_url, auth, headers)
        else:
            console.print(f"[{STYLES['error']}]Failed to create issue. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while creating the issue: {e}[/]")

def create_new_epic(jira_url, auth, headers, session, state):
    console.print(f"[{STYLES['search_result_header']}]Enter project key for the new epic (e.g., PROJ):[/]")
    project_key = session.prompt("> ").strip()
    if not project_key:
        console.print(f"[{STYLES['warning']}]Project key cannot be empty.[/]")
        return
    console.print(f"[{STYLES['search_result_header']}]Enter summary for the new epic:[/]")
    summary = session.prompt("> ").strip()
    console.print(f"[{STYLES['search_result_header']}]Enter description for the new epic:[/]")
    description = session.prompt("> ").strip()
    console.print(f"[{STYLES['search_result_header']}]Enter Epic Name:[/]")
    epic_name = session.prompt("> ").strip()
    if not summary or not epic_name:
        console.print(f"[{STYLES['warning']}]Summary and Epic Name cannot be empty.[/]")
        return
    # Prepare payload
    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "summary": summary,
            "description": description,
            "issuetype": {
                "name": "Epic"
            },
            epic_name_field_id: epic_name
        }
    }
    # Send POST request to create issue
    url = f"{jira_url}/rest/api/2/issue"
    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 201:
            new_issue = response.json()
            new_issue_key = new_issue.get('key')
            console.print(f"[{STYLES['success']}]Epic {new_issue_key} created successfully.[/]")
            state.update_last_ticket_key(new_issue_key)
            get_issue_details(new_issue_key, jira_url, auth, headers)
        else:
            console.print(f"[{STYLES['error']}]Failed to create epic. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while creating the epic: {e}[/]")

def link_issues(from_issue_key, to_issue_key, jira_url, auth, headers):
    url = f"{jira_url}/rest/api/2/issueLink"
    payload = {
        "type": {
            "name": "Relates"
        },
        "inwardIssue": {
            "key": to_issue_key
        },
        "outwardIssue": {
            "key": from_issue_key
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 201:
            console.print(f"[{STYLES['success']}]Linked {from_issue_key} to {to_issue_key} as 'Relates to'.[/]")
        else:
            console.print(f"[{STYLES['error']}]Failed to link issues. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while linking issues: {e}[/]")

def list_user_epics(jira_url, auth, headers):
    jql_query = 'issuetype = Epic AND reporter = currentUser() ORDER BY created DESC'
    params = {
        'jql': jql_query,
        'fields': 'key,summary,status,assignee,reporter',
        'maxResults': 50  # Adjust as needed
    }
    search_url = f"{jira_url}/rest/api/2/search"
    try:
        response = requests.get(search_url, headers=headers, auth=auth, params=params)
        if response.status_code == 200:
            search_results = response.json()
            issues = search_results.get('issues', [])
            if issues:
                console.print(f"[{STYLES['search_result_header']}]Your Epics:[/]")
                for issue in issues:
                    print_issue_summary(issue)
            else:
                console.print(f"[{STYLES['warning']}]No epics found reported by you.[/]")
        else:
            console.print(f"[{STYLES['error']}]Failed to retrieve epics. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while retrieving epics: {e}[/]")

def get_transitions(issue_key, jira_url, auth, headers):
    url = f"{jira_url}/rest/api/2/issue/{issue_key}/transitions"
    try:
        response = requests.get(url, headers=headers, auth=auth)
        if response.status_code == 200:
            data = response.json()
            transitions = data.get('transitions', [])
            return transitions
        else:
            console.print(f"[{STYLES['error']}]Failed to fetch transitions for issue {issue_key}. Status code: {response.status_code}[/]")
            return []
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while fetching transitions: {e}[/]")
        return []

def update_issue_status(issue_key, status_name, state, headers):
    if issue_key in state.statuses_cache:
        transitions = state.statuses_cache[issue_key]['transitions']
    else:
        transitions = get_transitions(issue_key, state.jira_url, state.auth, headers)
        statuses = [t['to']['name'] for t in transitions]
        state.statuses_cache[issue_key] = {'statuses': statuses, 'transitions': transitions}
    # Find the transition ID for the status_name
    transition_id = None
    for t in transitions:
        if t['to']['name'].lower() == status_name.lower():
            transition_id = t['id']
            break
    if not transition_id:
        console.print(f"[{STYLES['error']}]Transition to status '{status_name}' not found for issue {issue_key}.[/]")
        return

    url = f"{state.jira_url}/rest/api/2/issue/{issue_key}/transitions"
    payload = {
        "transition": {
            "id": transition_id
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, auth=state.auth)
        if response.status_code == 204:
            console.print(f"[{STYLES['success']}]Issue {issue_key} transitioned to '{status_name}' successfully.[/]")
            # Since status has changed, invalidate the cache for the issue
            state.statuses_cache.pop(issue_key, None)
        else:
            console.print(f"[{STYLES['error']}]Failed to transition issue {issue_key}. Status code: {response.status_code}[/]")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        console.print(f"[{STYLES['error']}]An error occurred while transitioning issue: {e}[/]")

if __name__ == '__main__':
    main()
