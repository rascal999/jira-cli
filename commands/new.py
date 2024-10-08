from rich.console import Console
from rich.prompt import Prompt
import os

console = Console()

def create_new_ticket(issue_manager, parent=None):
    try:
        if parent:
            # If parent is provided, fetch its details
            parent_issue = issue_manager.jira.issue(parent)
            selected_project = parent_issue.fields.project
            console.print(f"Creating a subtask for {parent} in project {selected_project.key}", style="cyan")
        else:
            # Fetch available projects
            projects = issue_manager.jira.projects()
            
            # Display available projects
            console.print("Available projects:", style="cyan")
            for idx, project in enumerate(projects, 1):
                console.print(f"{idx}. {project.key}: {project.name}")
            
            # Let user select a project
            while True:
                project_choice = Prompt.ask("Enter the number of the project", default="1")
                try:
                    project_index = int(project_choice) - 1
                    if 0 <= project_index < len(projects):
                        selected_project = projects[project_index]
                        break
                    else:
                        console.print("Invalid project number. Please try again.", style="yellow")
                except ValueError:
                    console.print("Please enter a valid number.", style="yellow")

        # Fetch project-specific information, including issue types
        project = issue_manager.jira.project(selected_project.key)
        issue_types = project.issueTypes

        if parent:
            # If parent is provided, only show subtask issue type
            issue_types = [it for it in issue_types if it.name.lower() == 'sub-task']
        else:
            # If no parent, exclude subtask from issue types
            issue_types = [it for it in issue_types if it.name.lower() != 'sub-task']

        summary = Prompt.ask("Enter issue summary")
        
        # Display available issue types for the selected project
        console.print("Available issue types:", style="cyan")
        for idx, issue_type in enumerate(issue_types, 1):
            console.print(f"{idx}. {issue_type.name}")
        
        # Let user select an issue type
        while True:
            type_choice = Prompt.ask("Enter the number of the issue type", default="1")
            try:
                type_index = int(type_choice) - 1
                if 0 <= type_index < len(issue_types):
                    selected_type = issue_types[type_index]
                    break
                else:
                    console.print("Invalid issue type number. Please try again.", style="yellow")
            except ValueError:
                console.print("Please enter a valid number.", style="yellow")

        # Check for a template file
        template_path = f"ticket_templates/{selected_type.name.lower().replace(' ', '_')}.txt"
        if os.path.exists(template_path):
            with open(template_path, 'r') as template_file:
                template_content = template_file.read()
            console.print(f"Template found for {selected_type.name}:", style="cyan")
            console.print(template_content)
            use_template = Prompt.ask("Use this template?", choices=["y", "n"], default="y")
            if use_template.lower() == 'y':
                description = template_content
            else:
                description = Prompt.ask("Enter issue description", default="")
        else:
            description = Prompt.ask("Enter issue description", default="")

        issue_dict = {
            'project': {'key': selected_project.key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': selected_type.name},
        }

        if parent:
            issue_dict['parent'] = {'key': parent}

        new_issue = issue_manager.jira.create_issue(fields=issue_dict)
        console.print(f"New issue created: {new_issue.key}", style="green")

        # Fetch and display the newly created issue
        fetched_issue = issue_manager.fetch_issue(new_issue.key)
        if fetched_issue:
            issue_manager.display_issue(fetched_issue)
        else:
            console.print(f"Failed to fetch the newly created issue {new_issue.key}", style="yellow")

        return new_issue

    except Exception as e:
        console.print(f"Error creating issue: {str(e)}", style="red")
        return None
