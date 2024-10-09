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
        tree = Tree(f"[cyan]{parent_issue.key}[/cyan]: {parent_issue.fields.summary}")
        child_node = tree.add(f"[cyan]{issue.key}[/cyan]: {issue.fields.summary}")
    else:
        tree = Tree(f"[cyan]{issue.key}[/cyan]: {issue.fields.summary}")
        child_node = tree

    build_subtree(issue_manager, issue, child_node)
    console.print(tree)

def get_parent_issue(issue_manager, issue):
    if hasattr(issue.fields, 'parent'):
        return issue_manager.fetch_issue(issue.fields.parent.key)
    elif hasattr(issue.fields, 'customfield_10014') and issue.fields.customfield_10014:
        return issue_manager.fetch_issue(issue.fields.customfield_10014)
    return None

def build_subtree(issue_manager, parent_issue, parent_node):
    subtasks = issue_manager.get_subtasks(parent_issue.key)
    for subtask in subtasks:
        node = parent_node.add(f"[cyan]{subtask.key}[/cyan]: {subtask.fields.summary}")
        build_subtree(issue_manager, subtask, node)

def execute(cli, arg):
    display_issue_tree(cli.issue_manager, arg)

COMMAND = "tree"
HELP = "Display issue tree starting from current or specified ticket."
