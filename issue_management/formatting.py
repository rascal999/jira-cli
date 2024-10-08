from rich.text import Text
import hashlib
import re

def format_issue_key(self, issue):
    project_key, issue_number = issue.key.split('-')
    project_color = self.get_project_color(project_key)
    return Text.assemble((project_key, project_color), "-", (issue_number, "bold"))

def format_status(self, status):
    return Text(status, style=self.get_status_color(status))

def format_assignee(self, assignee):
    if assignee:
        return Text(assignee.displayName, style=self.get_user_color(assignee.displayName))
    return Text("Unassigned", style="italic")

def format_issue_type(self, issue_type):
    short_type = issue_type[:8]  # Truncate to 8 characters
    return Text(short_type, style=self.get_color_for_string(issue_type, self.color_palette))

def get_color_from_string(self, s):
    hash_object = hashlib.md5(s.encode())
    hash_hex = hash_object.hexdigest()
    color = f"#{hash_hex[:6]}"
    return color

def get_color_for_string(self, s, color_list):
    hash_value = sum(ord(c) for c in s)
    return color_list[hash_value % len(color_list)]

def format_comment_body(self, body):
    mention_pattern = r'\[~accountid:([^\]]+)\]'
    
    formatted_text = Text()
    last_end = 0
    
    for match in re.finditer(mention_pattern, body):
        formatted_text.append(body[last_end:match.start()])
        
        account_id = match.group(1)
        display_name, color = self.resolve_user_mention(account_id)
        formatted_text.append(f"@{display_name}", style=color)
        
        last_end = match.end()
    
    formatted_text.append(body[last_end:])
    
    return formatted_text
