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

def run(args, current_ticket=None):
    console = Console()

    try:
        jira = get_jira_client()
        filters = jira.favourite_filters()

        if not filters:
            console.print("[yellow]No saved filters found on Jira.[/yellow]")
            return

        if not args:
            show_filters_table(console, filters)
        elif args[0].lower() in ['rm', 'del']:
            if len(args) < 2:
                console.print("[bold red]Error:[/bold red] Please specify a filter name to remove.")
            else:
                filter_name = ' '.join(args[1:])  # Join all arguments after 'rm' or 'del'
                remove_filter(console, jira, filters, filter_name)
        elif args[0].lower() == 'edit':
            if len(args) < 2:
                console.print("[bold red]Error:[/bold red] Please specify a filter name to edit.")
            else:
                filter_name = ' '.join(args[1:])
                edit_filter(console, jira, filters, filter_name)
        else:
            filter_name = ' '.join(args)
            run_matching_filter(console, filters, filter_name)

    except JIRAError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")

def show_filters_table(console, filters):
    table = Table(title="Saved Jira Filters")
    table.add_column("Name", style="magenta")
    table.add_column("JQL Query", style="green")

    sorted_filters = sorted(filters, key=lambda x: x.name.lower())

    for filter in sorted_filters:
        table.add_row(filter.name, filter.jql)

    console.print(table)

def run_matching_filter(console, filters, filter_name):
    matching_filter = find_matching_filter(console, filters, filter_name)
    if matching_filter:
        run_filter(console, matching_filter)

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

def edit_filter(console, jira, filters, filter_name):
    matching_filter = find_matching_filter(console, filters, filter_name)
    if matching_filter:
        # Create a temporary file with the current JQL query
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jql', delete=False) as temp_file:
            temp_file.write(matching_filter.jql)
            temp_file_path = temp_file.name

        # Open the temporary file in Vim
        subprocess.call(['vim', temp_file_path])

        # Read the updated content
        with open(temp_file_path, 'r') as temp_file:
            updated_jql = temp_file.read().strip()

        # Remove the temporary file
        os.unlink(temp_file_path)

        if updated_jql != matching_filter.jql:
            if confirm_action(f"Are you sure you want to update the filter '{matching_filter.name}'?"):
                try:
                    jira.update_filter(matching_filter.id, jql=updated_jql)
                    console.print(f"[bold green]Successfully updated filter: {matching_filter.name}[/bold green]")
                except JIRAError as e:
                    console.print(f"[bold red]Error updating filter:[/bold red] {str(e)}")
            else:
                console.print("[yellow]Filter update cancelled.[/yellow]")
        else:
            console.print("[yellow]No changes were made to the filter.[/yellow]")

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
    console.print(f"[cyan]JQL Query:[/cyan] {filter.jql}")
    jql.run([filter.jql])

HELP_TEXT = "Manage and run saved filters (Usage: rf [filter_name] or rf rm <filter_name>)"
ALIASES = ["rfilter", "rf"]
