import os
import tempfile
import subprocess
from rich.console import Console
from common.jira_client import get_jira_client
from common.cache_vid import vid_cache
from jira.exceptions import JIRAError

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket)

        # Get the current description (standard or custom)
        current_description = get_description(jira, issue)

        # Create a temporary file with the current description
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.tmp', delete=False) as temp_file:
            temp_file.write(current_description or '')
            temp_file_path = temp_file.name

        # Open the temporary file in Vim
        subprocess.call(['vim', temp_file_path])

        # Read the updated content
        with open(temp_file_path, 'r') as temp_file:
            updated_description = temp_file.read()

        # Remove the temporary file
        os.unlink(temp_file_path)

        # Update the issue description if it has changed
        if updated_description != current_description:
            try:
                update_description(jira, issue, updated_description)
                console.print(f"[bold green]Successfully updated description for {current_ticket}[/bold green]")
                
                # Update the cache
                vid_cache._update_cache(current_ticket, issue)
            except JIRAError as je:
                console.print(f"[bold red]Error:[/bold red] {str(je)}")
        else:
            console.print("[yellow]No changes were made to the description.[/yellow]")

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")
        console.print(f"[yellow]Debug info:[/yellow] {type(e).__name__}: {str(e)}")

def get_description(jira, issue):
    # Try to get the standard description first
    if hasattr(issue.fields, 'description') and issue.fields.description is not None:
        return issue.fields.description

    # If standard description is not available, look for a custom field
    custom_fields = [field for field in jira.fields() if 'description' in field['name'].lower()]
    for field in custom_fields:
        value = getattr(issue.fields, field['id'], None)
        if value:
            return value

    return ''  # Return empty string if no description field is found

def update_description(jira, issue, new_description):
    try:
        # Try updating the standard description field first
        issue.update(fields={'description': new_description})
    except JIRAError as je:
        if "Field 'description' cannot be set" in str(je):
            # If standard update fails, look for a custom description field
            custom_fields = [field for field in jira.fields() if 'description' in field['name'].lower()]
            for field in custom_fields:
                try:
                    issue.update(fields={field['id']: new_description})
                    return  # Exit the function if update is successful
                except JIRAError:
                    continue  # Try the next custom field if this one fails
            
            # If we've tried all custom fields and none worked, raise an exception
            raise JIRAError("Unable to update description. No writable description field found.")
        else:
            raise je  # Re-raise the original exception if it's not about setting the description

HELP_TEXT = "Open the current ticket's description in Vim for editing"
ALIASES = ["edit", "vim", "vi"]
