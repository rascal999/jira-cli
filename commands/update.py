import os
import tempfile
import subprocess
from rich.console import Console

console = Console()

def update_description(issue_manager, issue_key):
    try:
        issue = issue_manager.jira.issue(issue_key)
        current_description = issue.fields.description or ""

        # Create a temporary file with the current description
        with tempfile.NamedTemporaryFile(mode='w+', suffix=".tmp", delete=False) as temp_file:
            temp_file.write(current_description)
            temp_file_path = temp_file.name

        # Get the editor from environment variable, default to vim
        editor = os.getenv('EDITOR', 'vim')

        # Open the temporary file in the specified editor
        try:
            subprocess.call([editor, temp_file_path])
        except FileNotFoundError:
            console.print(f"Editor '{editor}' not found. Defaulting to vim.", style="yellow")
            subprocess.call(['vim', temp_file_path])

        # Read the updated content
        with open(temp_file_path, 'r') as temp_file:
            new_description = temp_file.read().strip()

        # Delete the temporary file
        os.unlink(temp_file_path)

        # Update the issue if the description has changed
        if new_description != current_description:
            issue.update(fields={'description': new_description})
            console.print(f"Updated description for {issue_key}", style="green")
        else:
            console.print("No changes made to the description.", style="yellow")

    except Exception as e:
        console.print(f"Error updating description for {issue_key}: {str(e)}", style="red")
