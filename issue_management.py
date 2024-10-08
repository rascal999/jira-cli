from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
import hashlib
from rich.tree import Tree
from jira import JIRA, JIRAError
from rich import box
from datetime import datetime
import re

class IssueManager:
    def __init__(self, jira_client):
        self.jira = jira_client
        self.console = Console()
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
            # Add more statuses and their corresponding colors here
        }

    def display_issue(self, issue):
        issue_text = Text()
        issue_text.append(f"{issue.key}: ", style="cyan bold")
        issue_text.append(f"{issue.fields.summary}\n\n", style="white bold")

        issue_text.append("Status: ", style="blue")
        issue_text.append(f"{issue.fields.status.name}\n", style=self.get_status_style(issue.fields.status.name))

        issue_text.append("Type: ", style="blue")
        issue_text.append(f"{issue.fields.issuetype.name}\n", style="magenta")

        issue_text.append("Priority: ", style="blue")
        issue_text.append(f"{issue.fields.priority.name}\n", style="yellow")

        issue_text.append("Assignee: ", style="blue")
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        issue_text.append(f"{assignee}\n", style="green")

        issue_text.append("Reporter: ", style="blue")
        issue_text.append(f"{issue.fields.reporter.displayName}\n", style="green")

        issue_text.append("Created: ", style="blue")
        issue_text.append(f"{issue.fields.created}\n", style="white")

        issue_text.append("Updated: ", style="blue")
        issue_text.append(f"{issue.fields.updated}\n\n", style="white")

        issue_text.append("Description:\n", style="blue bold")
        issue_text.append(f"{issue.fields.description or 'No description provided.'}\n", style="white")

        panel = Panel(issue_text, title=f"Issue Details: {issue.key}", expand=False, border_style="cyan")
        self.console.print(panel)

        # Display comments
        self.display_comments(issue.key)

    def display_comments(self, issue_key):
        comments = self.fetch_comments(issue_key)
        if comments:
            self.console.print("\nComments:", style="bold")
            for comment in comments:
                author_color = self.get_color_for_user(comment.author.displayName)
                comment_text = self.format_comment_body(comment.body)
                
                created_date = self.format_date(comment.created)
                title = Text()
                title.append(comment.author.displayName, style=f"bold {author_color}")
                title.append(f" - {created_date}", style="italic")
                
                panel = Panel(
                    comment_text,
                    title=title,
                    title_align="left",
                    border_style=author_color,
                    expand=False,
                    box=box.ROUNDED
                )
                self.console.print(panel)
                self.console.print()  # Add a blank line between comments
        else:
            self.console.print("No comments found for this issue.", style="yellow")

    def get_project_color(self, project_key):
        if project_key not in self.project_colors:
            hash_value = int(hashlib.md5(project_key.encode()).hexdigest(), 16)
            color_index = hash_value % len(self.color_palette)
            self.project_colors[project_key] = self.color_palette[color_index]
        return self.project_colors[project_key]

    def get_user_color(self, username):
        if username not in self.user_colors:
            hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
            color_index = hash_value % len(self.color_palette)
            self.user_colors[username] = self.color_palette[color_index]
        return self.user_colors[username]

    def get_status_color(self, status):
        return self.status_colors.get(status, "white")  # Default to white if status not found

    def format_issue_key(self, issue):
        project_key = issue.key.split('-')[0]
        issue_number = issue.key.split('-')[1]
        project_color = self.get_project_color(project_key)
        
        text = Text()
        text.append(f"{project_key}-", style=project_color)
        text.append(f"{issue_number}", style="bold")
        return text

    def format_status(self, status):
        color = self.get_status_color(status)
        return f"[{color}][{status}][/{color}]"

    def format_assignee(self, assignee):
        if assignee:
            color = self.get_user_color(assignee.displayName)
            return f"[{color}]{assignee.displayName}[/{color}]"
        return "Unassigned"

    def get_color_from_string(self, s):
        # Generate a hash of the string
        hash_object = hashlib.md5(s.encode())
        hash_hex = hash_object.hexdigest()
        
        # Use the first 6 characters of the hash as an RGB color
        color = f"#{hash_hex[:6]}"
        return color

    def format_issue_type(self, issue_type):
        color = self.get_color_from_string(issue_type)
        return Text(issue_type, style=color)

    def get_color_for_status(self, status):
        # Generate a hash of the status name
        hash_object = hashlib.md5(status.encode())
        hash_hex = hash_object.hexdigest()
        
        # Use the first 6 characters of the hash as an RGB color
        return f"#{hash_hex[:6]}"

    def get_color_for_string(self, string):
        # Generate a hash of the string
        hash_object = hashlib.md5(string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Use the first 6 characters of the hash as an RGB color
        return f"#{hash_hex[:6]}"

    def display_issues_table(self, issues, title):
        table = Table(title=title)
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Summary", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Assignee", style="blue")

        for issue in issues:
            # Color for Key (based on project)
            project_key = re.split('-', issue.key)[0]
            key_color = self.get_color_for_string(project_key)
            key_text = Text(issue.key, style=key_color)

            # Colors for Type, Status, and Assignee
            type_color = self.get_color_for_string(issue.fields.issuetype.name)
            status_color = self.get_color_for_string(issue.fields.status.name)
            assignee = getattr(issue.fields.assignee, 'displayName', 'Unassigned')
            assignee_color = self.get_color_for_string(assignee)

            type_text = Text(issue.fields.issuetype.name, style=type_color)
            status_text = Text(f"[{issue.fields.status.name}]", style=status_color)
            assignee_text = Text(assignee, style=assignee_color)
            
            table.add_row(
                key_text,
                type_text,
                issue.fields.summary,
                status_text,
                assignee_text
            )

        panel = Panel(table, expand=False, border_style="blue")
        self.console.print(panel)

    def get_user_epics(self):
        """List all epics reported by the current user."""
        try:
            current_user = self.jira.current_user()
            jql_query = f'reporter = {current_user} AND issuetype = Epic ORDER BY created DESC'
            epics = self.jira.search_issues(jql_query, maxResults=50, fields='summary,status,issuetype,assignee')
            self.display_issues_table(epics, "User Epics")
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

    def search_issues(self, query):
        try:
            issues = self.jira.search_issues(query)
            if issues:
                self.display_issues_table(issues, f"Search Results for '{query}'")
            else:
                self.console.print("No issues found matching the query.", style="yellow")
            return issues
        except Exception as e:
            self.console.print(f"Error searching for issues: {str(e)}", style="red")
            return []

    def create_new_issue(self, parent=None):
        try:
            # Fetch available projects
            projects = self.jira.projects()
            
            # Display available projects
            print("Available projects:")
            for idx, project in enumerate(projects, 1):
                print(f"{idx}. {project.key}: {project.name}")
            
            # Let user select a project
            while True:
                project_choice = input("Enter the number of the project: ")
                try:
                    project_index = int(project_choice) - 1
                    if 0 <= project_index < len(projects):
                        selected_project = projects[project_index]
                        break
                    else:
                        print("Invalid project number. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")

            # Fetch project-specific information, including issue types
            project = self.jira.project(selected_project.key)
            issue_types = project.issueTypes

            summary = input("Enter issue summary: ")
            description = input("Enter issue description: ")
            
            # Display available issue types for the selected project
            print("Available issue types:")
            for idx, issue_type in enumerate(issue_types, 1):
                print(f"{idx}. {issue_type.name}")
            
            # Let user select an issue type
            while True:
                type_choice = input("Enter the number of the issue type: ")
                try:
                    type_index = int(type_choice) - 1
                    if 0 <= type_index < len(issue_types):
                        selected_type = issue_types[type_index]
                        break
                    else:
                        print("Invalid issue type number. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")

            issue_dict = {
                'project': {'key': selected_project.key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': selected_type.name},
            }

            if parent:
                issue_dict['parent'] = {'key': parent}

            new_issue = self.jira.create_issue(fields=issue_dict)
            print(f"New issue created: {new_issue.key}")
            return new_issue.key
        except JIRAError as e:
            print(f"Error creating new issue: {str(e)}")
            return None

    def link_issues(self, from_issue, to_issue, link_type):
        try:
            self.jira.create_issue_link(link_type, from_issue, to_issue)
            print(f"Linked {from_issue} to {to_issue} with link type '{link_type}'")
        except JIRAError as e:
            print(f"Error linking issues: {str(e)}")

    def update_issue_description(self, issue_key, new_description):
        try:
            issue = self.jira.issue(issue_key)
            issue.update(fields={'description': new_description})
            print(f"Updated description for {issue_key}")
        except JIRAError as e:
            print(f"Error updating description for {issue_key}: {str(e)}")

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

    def get_issue_status_color(self, status_name):
        status_lower = status_name.lower()
        if 'closed' in status_lower or 'done' in status_lower or 'resolved' in status_lower:
            return 'green'
        elif 'in progress' in status_lower:
            return 'yellow'
        else:
            return 'red'

    def fetch_issue(self, issue_key):
        # Check if the issue_key matches the expected format (e.g., PROJ-123)
        if not re.match(r'^[A-Z]+-\d+$', issue_key):
            return None  # Return None for invalid issue key format

        try:
            return self.jira.issue(issue_key)
        except JIRAError as e:
            if e.status_code == 404:
                # Issue not found, but don't print an error message
                return None
            else:
                # For other errors, print the error message
                self.console.print(f"Error fetching issue {issue_key}: {str(e)}", style="red")
                return None

    def display_issue_tree(self, ticket_key, depth=0, max_depth=3):
        if depth >= max_depth:
            return None

        issue = self.fetch_issue(ticket_key)
        if not issue:
            self.console.print(f"Issue {ticket_key} not found.", style="red")
            return None

        tree = Tree(f"[cyan]{issue.key}[/cyan]: {issue.fields.summary}")

        # Add status
        status_text = Text(f"Status: {issue.fields.status.name}")
        status_text.stylize(self.get_status_style(issue.fields.status.name))
        tree.add(status_text)

        # Add assignee
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        tree.add(f"Assignee: {assignee}")

        # Recursively add subtasks
        subtasks = self.jira.search_issues(f'parent = {issue.key}')
        for subtask in subtasks:
            subtree = self.display_issue_tree(subtask.key, depth + 1, max_depth)
            if subtree:
                tree.add(subtree)

        if depth == 0:
            self.console.print(tree)
        return tree

    def get_status_style(self, status):
        status_styles = {
            "To Do": "bold blue",
            "In Progress": "bold yellow",
            "Done": "bold green",
            # Add more status mappings as needed
        }
        return status_styles.get(status, "white")

    def get_available_statuses(self, issue_key):
        try:
            issue = self.fetch_issue(issue_key)
            if not issue:
                return []
            
            transitions = self.jira.transitions(issue)
            return [t['name'] for t in transitions]
        except JIRAError as e:
            self.console.print(f"Error fetching available statuses for {issue_key}: {str(e)}", style="red")
            return []

    def fetch_comments(self, issue_key):
        try:
            issue = self.jira.issue(issue_key)
            return issue.fields.comment.comments
        except Exception as e:
            self.console.print(f"Error fetching comments for {issue_key}: {str(e)}", style="red")
            return []

    def get_color_for_user(self, username):
        color_hash = hashlib.md5(username.encode()).hexdigest()
        return f"#{color_hash[:6]}"

    def format_date(self, date_string):
        date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f%z")
        return date.strftime("%Y-%m-%d %H:%M")

    def resolve_user_mention(self, account_id):
        try:
            user = self.jira.user(account_id)
            display_name = user.displayName
            return (display_name, self.get_color_for_user(display_name))
        except:
            return (account_id, "white")  # Return the original account_id if resolution fails

    def format_comment_body(self, body):
        # Regular expression to match Jira user mentions
        mention_pattern = r'\[~accountid:([^\]]+)\]'
        
        formatted_text = Text()
        last_end = 0
        
        for match in re.finditer(mention_pattern, body):
            # Add text before the mention
            formatted_text.append(body[last_end:match.start()])
            
            # Resolve and add the mention
            account_id = match.group(1)
            display_name, color = self.resolve_user_mention(account_id)
            formatted_text.append(f"@{display_name}", style=color)
            
            last_end = match.end()
        
        # Add any remaining text after the last mention
        formatted_text.append(body[last_end:])
        
        return formatted_text