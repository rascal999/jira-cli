from rich.console import Console
from rich.table import Table
from common.jql_filters import load_jql_filters, save_jql_filters
from common.jql import perform_jql_search
from rapidfuzz import process, fuzz

def run(args, current_ticket=None):
    console = Console()
    filters = load_jql_filters()

    if not filters:
        console.print("[yellow]No saved filters found.[/yellow]")
        return []

    if not args:
        show_filters_table(console, filters)
        return []
    elif args[0].lower() in ['rm', 'del']:
        if len(args) < 2:
            console.print("[bold red]Error:[/bold red] Please specify a filter name to remove.")
        else:
            remove_filter(console, filters, ' '.join(args[1:]))
        return []
    else:
        filter_name = ' '.join(args)
        try:
            return run_matching_filter(console, filters, filter_name)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {str(e)}")
            return []

def show_filters_table(console, filters):
    table = Table(title="Saved JQL Filters")
    table.add_column("Name", style="magenta")
    table.add_column("JQL Query", style="green")

    sorted_filters = sorted(filters.items(), key=lambda x: x[0].lower())

    for name, query in sorted_filters:
        table.add_row(name, query)

    console.print(table)

def run_matching_filter(console, filters, filter_name):
    exact_match = filters.get(filter_name)
    if exact_match:
        return run_filter(console, filter_name, exact_match)

    # Partial matching
    partial_matches = [name for name in filters if filter_name.lower() in name.lower()]
    if len(partial_matches) == 1:
        return run_filter(console, partial_matches[0], filters[partial_matches[0]])
    elif len(partial_matches) > 1:
        console.print(f"[yellow]Multiple partial matches found for '{filter_name}':[/yellow]")
        for match in partial_matches:
            console.print(f"  - {match}")
        return []

    # Fuzzy matching
    fuzzy_matches = process.extract(filter_name, filters.keys(), scorer=fuzz.WRatio, limit=3)
    if fuzzy_matches and fuzzy_matches[0][1] >= 80:  # Check if there's a match and its score is >= 80
        best_match = fuzzy_matches[0][0]
        console.print(f"[yellow]Did you mean '{best_match}'? (y/n)[/yellow]")
        if console.input().lower() == 'y':
            return run_filter(console, best_match, filters[best_match])

    console.print(f"[bold red]Error:[/bold red] No matching filter found for '{filter_name}'.")
    return []

def run_filter(console, filter_name, jql_query):
    console.print(f"[bold cyan]Running filter:[/bold cyan] {filter_name}")
    console.print(f"[bold cyan]JQL Query:[/bold cyan] {jql_query}\n")
    return perform_jql_search(jql_query, ['key', 'summary', 'status', 'assignee'], max_results=30)

def remove_filter(console, filters, filter_name):
    exact_match = filters.get(filter_name)
    if exact_match:
        del filters[filter_name]
        save_jql_filters(filters)
        console.print(f"[bold green]Filter '{filter_name}' has been removed.[/bold green]")
        return

    # Partial matching
    partial_matches = [name for name in filters if filter_name.lower() in name.lower()]
    if len(partial_matches) == 1:
        del filters[partial_matches[0]]
        save_jql_filters(filters)
        console.print(f"[bold green]Filter '{partial_matches[0]}' has been removed.[/bold green]")
        return
    elif len(partial_matches) > 1:
        console.print(f"[yellow]Multiple partial matches found for '{filter_name}':[/yellow]")
        for match in partial_matches:
            console.print(f"  - {match}")
        console.print("[yellow]Please specify the exact filter name to remove.[/yellow]")
        return

    # Fuzzy matching
    fuzzy_matches = process.extract(filter_name, filters.keys(), scorer=fuzz.WRatio, limit=1)
    if fuzzy_matches:
        best_match, score = fuzzy_matches[0]
        if score >= 80:  # You can adjust this threshold
            console.print(f"[yellow]Did you mean '{best_match}'? (y/n)[/yellow]")
            if console.input().lower() == 'y':
                del filters[best_match]
                save_jql_filters(filters)
                console.print(f"[bold green]Filter '{best_match}' has been removed.[/bold green]")
                return

    console.print(f"[bold red]Error:[/bold red] No matching filter found for '{filter_name}'.")

HELP_TEXT = "Display saved JQL filters, run a specific filter, or remove a filter (Usage: filter [filter_name] | filter rm/del [filter_name])"
ALIASES = ["filters", "f"]
