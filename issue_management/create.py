import os
from rich.console import Console
from jira import JIRA

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

        # Check for a template file
        template_path = f"ticket_templates/{selected_type.name.lower().replace(' ', '_')}.txt"
        if os.path.exists(template_path):
            with open(template_path, 'r') as template_file:
                template_content = template_file.read()
            print(f"Template found for {selected_type.name}:")
            print(template_content)
            use_template = input("Use this template? (Y/n): ").lower() != 'n'
            if use_template:
                description = template_content
            else:
                description = input("Enter issue description: ")
        else:
            description = input("Enter issue description: ")

        issue_dict = {
            'project': {'key': selected_project.key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': selected_type.name},
        }

        if parent:
            issue_dict['parent'] = {'key': parent}

        new_issue = self.jira.create_issue(fields=issue_dict)
        self.console.print(f"New issue created: {new_issue.key}", style="green")
        return new_issue
    except Exception as e:
        self.console.print(f"Error creating issue: {str(e)}", style="red")
