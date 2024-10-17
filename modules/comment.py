import os
import tempfile
import subprocess
from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from rapidfuzz import process, fuzz
import re
import requests

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Create a temporary file for the comment
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.tmp', delete=False) as temp_file:
            temp_file_path = temp_file.name

        # Open the temporary file in Vim
        subprocess.call(['vim', temp_file_path])

        # Read the comment content
        with open(temp_file_path, 'r') as temp_file:
            comment_body = temp_file.read().strip()

        # Remove the temporary file
        os.unlink(temp_file_path)

        # Process user mentions
        comment_body = process_user_mentions(comment_body, jira)

        # Add the comment if it's not empty
        if comment_body:
            jira.add_comment(issue, comment_body)
            console.print(f"[bold green]Successfully added comment to {current_ticket}[/bold green]")
        else:
            console.print("[yellow]No comment was added (empty comment)[/yellow]")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")

def process_user_mentions(comment_body, jira):
    console = Console()
    resolved_users = []
    unresolved_users = []

    def replace_mention(match):
        user_name = match.group(1)
        
        api_endpoint = f"{jira._options['server']}/rest/api/3/user/search"
        params = {'query': user_name}
        response = requests.get(
            api_endpoint,
            params=params,
            auth=jira._session.auth
        )
        
        if response.status_code == 200:
            users = response.json()
            if users:
                best_match = process.extractOne(user_name, [user['displayName'] for user in users], scorer=fuzz.ratio)
                if best_match and best_match[1] > 80:  # 80% similarity threshold
                    matched_user = next(user for user in users if user['displayName'] == best_match[0])
                    resolved_users.append(f"{user_name} -> {matched_user['displayName']} (Account ID: {matched_user['accountId']})")
                    return f"[~accountid:{matched_user['accountId']}]"
                else:
                    unresolved_users.append(user_name)
            else:
                unresolved_users.append(user_name)
        else:
            unresolved_users.append(user_name)
        
        return match.group(0)  # Return the original string if no match found

    pattern = r'\[\[(.*?)\]\]'
    result = re.sub(pattern, replace_mention, comment_body)

    if resolved_users:
        console.print("[green]Successfully resolved user mentions:[/green]")
        for user in resolved_users:
            console.print(f"  - {user}")

    if unresolved_users:
        console.print("[yellow]Unable to resolve the following user mentions:[/yellow]")
        for user in unresolved_users:
            console.print(f"  - {user}")

    return result

HELP_TEXT = "Add a comment to the current ticket using Vim"
