import os
import importlib
from rich.console import Console
from common.table import create_jira_table, add_row_to_table, print_table

def run(args=None):
    console = Console()
    table = create_jira_table("Available Commands", ["Command", "Description"])

    modules_dir = os.path.dirname(__file__)
    module_list = []
    for filename in os.listdir(modules_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            module = importlib.import_module(f'modules.{module_name}')
            help_text = getattr(module, 'HELP_TEXT', "No help text available")
            module_list.append((module_name, help_text))

    module_list.sort(key=lambda x: x[0])

    color_map = {}
    for module_name, help_text in module_list:
        add_row_to_table(table, type('obj', (object,), {'key': module_name, 'fields': type('obj', (object,), {'command': module_name, 'description': help_text})}), ['command', 'description'], color_map)

    print_table(console, table)

HELP_TEXT = "Display this help message"
