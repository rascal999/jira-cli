from rich.console import Console
from rich.tree import Tree

console = Console()

def display_issue_tree(issue_manager, ticket=None):
    if not ticket:
        ticket = issue_manager.current_ticket
    
    if not ticket:
        console.print("No ticket specified or currently focused.", style="yellow")
        return

    issue = issue_manager.fetch_issue(ticket)
    if not issue:
        console.print(f"Failed to fetch issue {ticket}", style="red")
        return

    # Start with the parent issue
    parent_issue = get_parent_issue(issue_manager, issue)
    if parent_issue:
        tree = Tree(f"[cyan]{parent_issue['key'] if isinstance(parent_issue, dict) else parent_issue.key}[/cyan]: {parent_issue['fields']['summary'] if isinstance(parent_issue, dict) else parent_issue.fields.summary}")
        child_node = tree.add(f"[cyan]{issue['key'] if isinstance(issue, dict) else issue.key}[/cyan]: {issue['fields']['summary'] if isinstance(issue, dict) else issue.fields.summary}")
    else:
        tree = Tree(f"[cyan]{issue['key'] if isinstance(issue, dict) else issue.key}[/cyan]: {issue['fields']['summary'] if isinstance(issue, dict) else issue.fields.summary}")
        child_node = tree

    build_subtree(issue_manager, issue, child_node)
    console.print(tree)

def get_parent_issue(issue_manager, issue):
    if isinstance(issue, dict):
        if 'fields' in issue and 'parent' in issue['fields']:
            return issue_manager.fetch_issue(issue['fields']['parent']['key'])
        elif 'fields' in issue and 'customfield_10014' in issue['fields'] and issue['fields']['customfield_10014']:
            return issue_manager.fetch_issue(issue['fields']['customfield_10014'])
    else:
        if hasattr(issue.fields, 'parent'):
            return issue_manager.fetch_issue(issue.fields.parent.key)
        elif hasattr(issue.fields, 'customfield_10014') and issue.fields.customfield_10014:
            return issue_manager.fetch_issue(issue.fields.customfield_10014)
    return None

def build_subtree(issue_manager, parent_issue, parent_node):
    # Check for subtasks
    parent_key = parent_issue['key'] if isinstance(parent_issue, dict) else parent_issue.key
    subtasks = issue_manager.get_subtasks(parent_key)
    for subtask in subtasks:
        subtask_key = subtask['key'] if isinstance(subtask, dict) else subtask.key
        subtask_summary = subtask['fields']['summary'] if isinstance(subtask, dict) else subtask.fields.summary
        node = parent_node.add(f"[cyan]{subtask_key}[/cyan]: {subtask_summary}")
        build_subtree(issue_manager, subtask, node)
    
    # Check for epic children (if the current issue is an epic)
    if isinstance(parent_issue, dict):
        issue_type = parent_issue['fields']['issuetype']['name'].lower()
    else:
        issue_type = parent_issue.fields.issuetype.name.lower()
    
    if issue_type == 'epic':
        epic_children = issue_manager.get_epic_children(parent_key)
        for child in epic_children:
            child_key = child['key'] if isinstance(child, dict) else child.key
            child_summary = child['fields']['summary'] if isinstance(child, dict) else child.fields.summary
            node = parent_node.add(f"[green]{child_key}[/green]: {child_summary}")
            build_subtree(issue_manager, child, node)

def execute(cli, arg):
    if arg:
        ticket = arg
    elif cli.current_ticket:
        ticket = cli.current_ticket
    else:
        ticket = None
    
    display_issue_tree(cli.issue_manager, ticket)

COMMAND = "tree"
HELP = "Display issue tree starting from current or specified ticket."
