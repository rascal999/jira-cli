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

    tree = Tree(f"[cyan]{issue.key}[/cyan]: {issue.fields.summary}")
    build_subtree(issue_manager, issue, tree)
    console.print(tree)

def build_subtree(issue_manager, parent_issue, parent_node):
    subtasks = issue_manager.get_subtasks(parent_issue.key)
    for subtask in subtasks:
        node = parent_node.add(f"[cyan]{subtask.key}[/cyan]: {subtask.fields.summary}")
        build_subtree(issue_manager, subtask, node)
