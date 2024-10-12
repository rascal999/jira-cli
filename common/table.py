from rich.console import Console
from rich.table import Table
from rich.text import Text
import hashlib

def get_color_for_value(value):
    colors = ["red", "green", "blue", "magenta", "cyan", "yellow", "orange", "purple", "pink"]
    hash_value = int(hashlib.md5(str(value).encode()).hexdigest(), 16)
    color_index = hash_value % len(colors)
    return colors[color_index]

def is_date_time_field(field_name):
    date_time_fields = ['created', 'updated', 'resolutiondate', 'duedate']
    return field_name.lower() in date_time_fields

def create_jira_table(title, fields_to_display):
    table = Table(title=title)
    for field in fields_to_display:
        table.add_column(field.capitalize(), style="cyan")
    return table

def add_row_to_table(table, issue, fields_to_display, color_map):
    row = []
    row_style = None
    for field in fields_to_display:
        if field == 'key':
            value = issue.key
            project_id = value.split('-')[0]
            if project_id not in color_map:
                color_map[project_id] = get_color_for_value(project_id)
            color = color_map[project_id]
            str_value = Text(value, style=color)
        else:
            value = getattr(issue.fields, field, "N/A")
            if hasattr(value, 'name'):
                value = value.name
            
            str_value = str(value)

            column_name = field.capitalize()
            if column_name not in ['Summary', 'Description', 'Command'] and not is_date_time_field(field):
                if str_value not in color_map:
                    color_map[str_value] = get_color_for_value(str_value)
                color = color_map[str_value]
                str_value = Text(str_value, style=color)
            else:
                # If we're not coloring by field value, we'll use alternating row styles
                if row_style is None:
                    row_style = "yellow" if len(table.rows) % 2 == 0 else None

        row.append(str_value)
    table.add_row(*row, style=row_style)

def print_table(console, table):
    console.print(table)
