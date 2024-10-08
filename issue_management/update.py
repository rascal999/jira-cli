from jira import JIRAError
import os
import tempfile
import subprocess
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def update_issue_description(self, issue_key):
    try:
        issue = self.jira.issue(issue_key)
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
            self.console.print(f"Editor '{editor}' not found. Defaulting to vim.", style="yellow")
            subprocess.call(['vim', temp_file_path])

        # Read the updated content
        with open(temp_file_path, 'r') as temp_file:
            new_description = temp_file.read().strip()

        # Delete the temporary file
        os.unlink(temp_file_path)

        # Update the issue if the description has changed
        if new_description != current_description:
            issue.update(fields={'description': new_description})
            self.console.print(f"Updated description for {issue_key}", style="green")
        else:
            self.console.print("No changes made to the description.", style="yellow")

    except Exception as e:
        self.console.print(f"Error updating description for {issue_key}: {str(e)}", style="red")

def link_issues(self, from_issue, to_issue):
    try:
        # Fetch the current issue to check existing links
        issue = self.jira.issue(from_issue)
        
        # Check if the issues are already linked
        existing_link = next((link for link in issue.fields.issuelinks 
                                if (hasattr(link, 'outwardIssue') and link.outwardIssue.key == to_issue) or
                                   (hasattr(link, 'inwardIssue') and link.inwardIssue.key == to_issue)), None)
        
        if existing_link:
            # If already linked, unlink the issues
            self.jira.delete_issue_link(existing_link.id)
            self.console.print(f"Unlinked {from_issue} from {to_issue}", style="green")
            return

        # If not linked, proceed with linking
        link_types = self.jira.issue_link_types()
        
        if not link_types:
            self.console.print("No link types available.", style="yellow")
            return

        # Display available link types
        self.console.print("Available link types:", style="cyan")
        for idx, lt in enumerate(link_types, 1):
            self.console.print(f"{idx}. {lt.outward} / {lt.inward}", style="white")
        
        # Ask user to choose a link type
        choice = input("Enter the number of the link type you want to use: ")
        try:
            chosen_link_type = link_types[int(choice) - 1]
        except (ValueError, IndexError):
            self.console.print("Invalid choice. Using the first available link type.", style="yellow")
            chosen_link_type = link_types[0]

        # Create the link
        self.jira.create_issue_link(
            type=chosen_link_type.name,
            inwardIssue=from_issue,
            outwardIssue=to_issue
        )
        self.console.print(f"Linked {from_issue} to {to_issue} with link type '{chosen_link_type.outward}'", style="green")
    except Exception as e:
        self.console.print(f"Error managing issue link: {str(e)}", style="red")

def update_issue_description(self, issue_key):
    try:
        issue = self.jira.issue(issue_key)
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
            self.console.print(f"Editor '{editor}' not found. Defaulting to vim.", style="yellow")
            subprocess.call(['vim', temp_file_path])

        # Read the updated content
        with open(temp_file_path, 'r') as temp_file:
            new_description = temp_file.read().strip()

        # Delete the temporary file
        os.unlink(temp_file_path)

        # Update the issue if the description has changed
        if new_description != current_description:
            issue.update(fields={'description': new_description})
            self.console.print(f"Updated description for {issue_key}", style="green")
        else:
            self.console.print("No changes made to the description.", style="yellow")

    except Exception as e:
        self.console.print(f"Error updating description for {issue_key}: {str(e)}", style="red")

def get_parent_issue(self, issue_key):
    try:
        issue = self.jira.issue(issue_key)
        if hasattr(issue.fields, 'parent'):
            return issue.fields.parent
        elif hasattr(issue.fields, 'customfield_10014'):  # Epic link field
            return self.jira.issue(issue.fields.customfield_10014)
        else:
            print(f"No parent found for {issue_key}")
            return None
    except JIRAError as e:
        print(f"Error getting parent for {issue_key}: {str(e)}")
        return None

def update_issue_summary(self, issue_key, new_summary):
    try:
        issue = self.jira.issue(issue_key)
        issue.update(fields={'summary': new_summary})
        print(f"Updated summary for {issue_key}")
    except JIRAError as e:
        print(f"Error updating summary for {issue_key}: {str(e)}")
