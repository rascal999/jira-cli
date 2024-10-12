import os
import webbrowser
from rich.console import Console
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
import json
import csv
import xml.etree.ElementTree as ET
import html

def is_json(value):
    try:
        json.loads(value)
        return True
    except (ValueError, TypeError):
        return False

def run(args, current_ticket=None):
    console = Console()

    if not current_ticket:
        console.print("[bold red]Error:[/bold red] No current ticket is focused. Use 'vid' command to focus on a ticket first.")
        return

    if not args:
        console.print("[bold red]Error:[/bold red] Please specify a file format (json, csv, xml, or html).")
        return

    file_format = args[0].lower()
    if file_format not in ['json', 'csv', 'xml', 'html']:
        console.print("[bold red]Error:[/bold red] Unsupported file format. Please use json, csv, xml, or html.")
        return

    try:
        jira = get_jira_client()
        issue = jira.issue(current_ticket, expand='comments,subtasks,attachments')
        
        # Fetch additional information
        child_tasks = jira.search_issues(f'parent = {current_ticket}')
        related_issues = jira.search_issues(f'issue in linkedIssues("{current_ticket}")')

        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.getcwd(), 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        file_name = os.path.join(reports_dir, f"{current_ticket}.{file_format}")
        
        if file_format == 'json':
            export_json(issue, child_tasks, related_issues, file_name)
        elif file_format == 'csv':
            export_csv(issue, child_tasks, related_issues, file_name)
        elif file_format == 'xml':
            export_xml(issue, child_tasks, related_issues, file_name)
        elif file_format == 'html':
            export_html(issue, child_tasks, related_issues, file_name)

        console.print(f"[bold green]Successfully exported {current_ticket} to {file_name}[/bold green]")

        if file_format == 'html':
            webbrowser.open(f"file://{os.path.abspath(file_name)}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")

def get_relevant_fields(issue):
    relevant_fields = {}
    for key, value in issue.raw['fields'].items():
        if value and not key.startswith('customfield_'):
            field_name = key.replace('_', ' ').title()
            if isinstance(value, dict) and 'name' in value:
                relevant_fields[field_name] = value['name']
            elif isinstance(value, list) and all(isinstance(item, dict) and 'name' in item for item in value):
                relevant_fields[field_name] = ', '.join(item['name'] for item in value)
            elif isinstance(value, str) and not is_json(value):
                relevant_fields[field_name] = value
            elif not isinstance(value, (dict, list)):
                relevant_fields[field_name] = str(value)
    return relevant_fields

def export_json(issue, child_tasks, related_issues, file_name):
    data = {
        'key': issue.key,
        'fields': get_relevant_fields(issue),
        'comments': [{'author': c.author.displayName, 'body': c.body} for c in issue.fields.comment.comments] if issue.fields.comment.comments else None,
        'subtasks': [{'key': st.key, 'summary': st.fields.summary} for st in issue.fields.subtasks] if issue.fields.subtasks else None,
        'attachments': [{'filename': a.filename, 'size': a.size} for a in issue.fields.attachment] if issue.fields.attachment else None,
        'child_tasks': [{'key': ct.key, 'summary': ct.fields.summary} for ct in child_tasks] if child_tasks else None,
        'related_issues': [{'key': ri.key, 'summary': ri.fields.summary} for ri in related_issues] if related_issues else None
    }
    data = {k: v for k, v in data.items() if v}  # Remove empty components
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=2)

def export_csv(issue, child_tasks, related_issues, file_name):
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Field', 'Value'])
        for key, value in get_relevant_fields(issue).items():
            writer.writerow([key, value])
        
        if issue.fields.comment.comments:
            writer.writerow(['', ''])
            writer.writerow(['Comments', ''])
            for comment in issue.fields.comment.comments:
                writer.writerow([comment.author.displayName, comment.body])
        
        if issue.fields.subtasks:
            writer.writerow(['', ''])
            writer.writerow(['Subtasks', ''])
            for subtask in issue.fields.subtasks:
                writer.writerow([subtask.key, subtask.fields.summary])
        
        if issue.fields.attachment:
            writer.writerow(['', ''])
            writer.writerow(['Attachments', ''])
            for attachment in issue.fields.attachment:
                writer.writerow([attachment.filename, f"{attachment.size} bytes"])
        
        if child_tasks:
            writer.writerow(['', ''])
            writer.writerow(['Child Tasks', ''])
            for child in child_tasks:
                writer.writerow([child.key, child.fields.summary])
        
        if related_issues:
            writer.writerow(['', ''])
            writer.writerow(['Related Issues', ''])
            for related in related_issues:
                writer.writerow([related.key, related.fields.summary])

def export_xml(issue, child_tasks, related_issues, file_name):
    root = ET.Element("issue")
    ET.SubElement(root, "key").text = issue.key
    fields = ET.SubElement(root, "fields")
    for key, value in get_relevant_fields(issue).items():
        field = ET.SubElement(fields, "field")
        field.set("name", key)
        field.text = value
    
    if issue.fields.comment.comments:
        comments = ET.SubElement(root, "comments")
        for comment in issue.fields.comment.comments:
            c = ET.SubElement(comments, "comment")
            ET.SubElement(c, "author").text = comment.author.displayName
            ET.SubElement(c, "body").text = comment.body
    
    if issue.fields.subtasks:
        subtasks = ET.SubElement(root, "subtasks")
        for subtask in issue.fields.subtasks:
            st = ET.SubElement(subtasks, "subtask")
            ET.SubElement(st, "key").text = subtask.key
            ET.SubElement(st, "summary").text = subtask.fields.summary
    
    if issue.fields.attachment:
        attachments = ET.SubElement(root, "attachments")
        for attachment in issue.fields.attachment:
            a = ET.SubElement(attachments, "attachment")
            ET.SubElement(a, "filename").text = attachment.filename
            ET.SubElement(a, "size").text = str(attachment.size)
    
    if child_tasks:
        child_tasks_elem = ET.SubElement(root, "child_tasks")
        for child in child_tasks:
            ct = ET.SubElement(child_tasks_elem, "child_task")
            ET.SubElement(ct, "key").text = child.key
            ET.SubElement(ct, "summary").text = child.fields.summary
    
    if related_issues:
        related_issues_elem = ET.SubElement(root, "related_issues")
        for related in related_issues:
            ri = ET.SubElement(related_issues_elem, "related_issue")
            ET.SubElement(ri, "key").text = related.key
            ET.SubElement(ri, "summary").text = related.fields.summary
    
    tree = ET.ElementTree(root)
    tree.write(file_name, encoding='utf-8', xml_declaration=True)

def export_html(issue, child_tasks, related_issues, file_name):
    html_content = f"""
    <html>
    <head>
        <title>Issue {issue.key}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            h1, h2 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Issue {issue.key}</h1>
        <h2>Fields</h2>
        <table>
            <tr>
                <th>Field</th>
                <th>Value</th>
            </tr>
    """

    for key, value in get_relevant_fields(issue).items():
        html_content += f"""
            <tr>
                <td>{html.escape(key)}</td>
                <td>{html.escape(value)}</td>
            </tr>
        """

    html_content += """
        </table>
    """

    if issue.fields.comment.comments:
        html_content += """
            <h2>Comments</h2>
            <table>
                <tr>
                    <th>Author</th>
                    <th>Comment</th>
                </tr>
        """

        for comment in issue.fields.comment.comments:
            html_content += f"""
                <tr>
                    <td>{html.escape(comment.author.displayName)}</td>
                    <td>{html.escape(comment.body)}</td>
                </tr>
            """

        html_content += """
            </table>
        """

    if issue.fields.subtasks:
        html_content += """
            <h2>Subtasks</h2>
            <table>
                <tr>
                    <th>Key</th>
                    <th>Summary</th>
                </tr>
        """

        for subtask in issue.fields.subtasks:
            html_content += f"""
                <tr>
                    <td>{html.escape(subtask.key)}</td>
                    <td>{html.escape(subtask.fields.summary)}</td>
                </tr>
            """

        html_content += """
            </table>
        """

    if issue.fields.attachment:
        html_content += """
            <h2>Attachments</h2>
            <table>
                <tr>
                    <th>Filename</th>
                    <th>Size</th>
                </tr>
        """

        for attachment in issue.fields.attachment:
            html_content += f"""
                <tr>
                    <td>{html.escape(attachment.filename)}</td>
                    <td>{attachment.size} bytes</td>
                </tr>
            """

        html_content += """
            </table>
        """

    if child_tasks:
        html_content += """
            <h2>Child Tasks</h2>
            <table>
                <tr>
                    <th>Key</th>
                    <th>Summary</th>
                </tr>
        """

        for child in child_tasks:
            html_content += f"""
                <tr>
                    <td>{html.escape(child.key)}</td>
                    <td>{html.escape(child.fields.summary)}</td>
                </tr>
            """

        html_content += """
            </table>
        """

    if related_issues:
        html_content += """
            <h2>Related Issues</h2>
            <table>
                <tr>
                    <th>Key</th>
                    <th>Summary</th>
                </tr>
        """

        for related in related_issues:
            html_content += f"""
                <tr>
                    <td>{html.escape(related.key)}</td>
                    <td>{html.escape(related.fields.summary)}</td>
                </tr>
            """

        html_content += """
            </table>
        """

    html_content += """
    </body>
    </html>
    """

    with open(file_name, 'w') as f:
        f.write(html_content)

HELP_TEXT = "Export the current ticket to a specified file format (json, csv, xml, or html) in the ./reports/ directory, including relevant fields, comments, subtasks, attachments, child tasks, and related issues"
