import tempfile
import subprocess
import os
from rich.console import Console
from rich.table import Table
from common.jira_client import get_jira_client
from jira.exceptions import JIRAError
from modules import jql
from rapidfuzz import process, fuzz
from common.utils import confirm_action
from jira import JIRA
from common.jql import perform_jql_search

def run(args, current_ticket=None):
    console = Console()
    jira = get_jira_client()

    try:
        filters = jira.favourite_filters()
    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] Unable to fetch filters: {str(e)}")
        return []

    if not filters:
        console.print("[yellow]No saved remote filters found.[/yellow]")
        return []

    if not args:
        show_filters_table(console, filters)
        return []
    elif args[0].lower() in ['rm', 'del']:
        if len(args) < 2:
            console.print("[bold red]Error:[/bold red] Please specify a filter name to remove.")
        else:
            remove_filter(console, jira, filters, ' '.join(args[1:]))
        return []
    elif args[0].lower() == 'edit':
        if len(args) < 2:
            console.print("[bold red]Error:[/bold red] Please specify a filter name to edit.")
        else:
            return run_matching_filter(console, jira, filters, ' '.join(args[1:]), edit_mode=True)
    else:
        filter_name = ' '.join(args)
        return run_matching_filter(console, jira, filters, filter_name)

def show_filters_table(console, filters):
    table = Table(title="Saved Jira Filters")
    table.add_column("Name", style="magenta")
    table.add_column("JQL Query", style="green")

    sorted_filters = sorted(filters, key=lambda x: x.name.lower())

    for filter in sorted_filters:
        table.add_row(filter.name, filter.jql)

    console.print(table)

def run_matching_filter(console, jira, filters, filter_name, edit_mode=False):
    matching_filter = find_matching_filter(console, filters, filter_name)
    if matching_filter:
        if edit_mode:
            edit_filter(console, jira, matching_filter)
            return []
        else:
            return run_filter(console, matching_filter)
    return []

def remove_filter(console, jira, filters, filter_name):
    best_match = process.extractOne(filter_name, [f.name for f in filters], scorer=fuzz.ratio)
    if best_match and best_match[1] > 80:  # 80% similarity threshold
        matching_filter = next(f for f in filters if f.name == best_match[0])
        
        if confirm_action(f"Are you sure you want to delete the filter '{matching_filter.name}'?"):
            try:
                matching_filter.delete()
                console.print(f"[bold green]Successfully deleted filter: {matching_filter.name}[/bold green]")
            except AttributeError:
                console.print("[bold red]Error:[/bold red] Unable to delete the filter. The JIRA API might have changed.")
        else:
            console.print("[yellow]Filter deletion cancelled.[/yellow]")
    else:
        console.print(f"[bold red]Error:[/bold red] No filter found matching '{filter_name}'.")

def edit_filter(console, jira, filter):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.jql', delete=False) as temp_file:
        temp_file.write(filter.jql)
        temp_file_path = temp_file.name

    subprocess.call(['vim', temp_file_path])

    with open(temp_file_path, 'r') as temp_file:
        new_jql = temp_file.read().strip()

    if new_jql != filter.jql:
        try:
            jira.update_filter(filter.id, jql=new_jql)
            console.print(f"[bold green]Successfully updated filter '{filter.name}'[/bold green]")
        except JIRAError as e:
            console.print(f"[bold red]Error updating filter:[/bold red] {str(e)}")
    else:
        console.print("[yellow]No changes made to the filter.[/yellow]")

def find_matching_filter(console, filters, filter_name):
    # Exact match
    exact_match = next((f for f in filters if f.name.lower() == filter_name.lower()), None)
    if exact_match:
        return exact_match

    # Partial matching
    partial_matches = [f for f in filters if filter_name.lower() in f.name.lower()]
    if len(partial_matches) == 1:
        return partial_matches[0]
    elif len(partial_matches) > 1:
        console.print(f"[yellow]Multiple partial matches found for '{filter_name}':[/yellow]")
        for match in partial_matches:
            console.print(f"  - {match.name}")
        return None

    # Fuzzy matching
    filter_names = [f.name for f in filters]
    fuzzy_matches = process.extract(filter_name, filter_names, scorer=fuzz.WRatio, limit=3)
    if fuzzy_matches and fuzzy_matches[0][1] >= 80:  # Check if there's a match and its score is >= 80
        best_match = next(f for f in filters if f.name == fuzzy_matches[0][0])
        console.print(f"[yellow]Did you mean '{best_match.name}'? (y/n)[/yellow]")
        if console.input().lower() == 'y':
            return best_match

    console.print(f"[bold red]Error:[/bold red] No matching filter found for '{filter_name}'.")
    return None

def run_filter(console, filter):
    console.print(f"[bold cyan]Running filter:[/bold cyan] {filter.name}")
    console.print(f"[bold cyan]JQL Query:[/bold cyan] {filter.jql}\n")
    return perform_jql_search(filter.jql, ['key', 'summary', 'status', 'assignee'], max_results=30)

HELP_TEXT = "Display saved remote JQL filters, run a specific filter, edit a filter, or remove a filter (Usage: rfilter [filter_name] | rfilter edit [filter_name] | rfilter rm/del [filter_name])"
ALIASES = ["rfilters", "rf"]
