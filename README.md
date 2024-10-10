# Jira CLI

A command-line interface tool for interacting with Jira, featuring AI integration and enhanced productivity features.

## Features

- Interactive command-line interface for Jira
- Search and display Jira issues
- Create, update, and delete issues
- Add comments to issues
- View and manage epics
- AI-powered assistance for Jira tasks
- Clipboard integration for quick access to issue URLs
- Customizable issue display and formatting

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/jira-cli.git
   cd jira-cli
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```
   cp .env-example .env
   ```
   Edit the `.env` file with your Jira and OpenAI API credentials.

## Usage

Run the CLI:

```
python main.py
```

When no initial ticket or search string is provided, the interactive shell will start.

```
                             Available Commands
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command  ┃ Description                                                   ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ /epics   │ List all epics reported by you.                               │
│ /grab    │ Copy URL of current or specified issue to clipboard.          │
│ /link    │ Link current ticket to specified ticket or unlink if already  │
│          │ linked. Usage: /link TICKET_ID                                │
│ /update  │ Update the description of the current ticket.                 │
│ /help    │ Show this help message.                                       │
│ /quit    │ Quit the program.                                             │
│ /recent  │ Display recently updated issues reported by you.              │
│ /clear   │ Clear the current focused ticket.                             │
│ /search  │ Search for issues using JQL.                                  │
│ /hello   │ Print 'Hello World!' to the console                           │
│ /parent  │ Change focus to parent ticket and display its details.        │
│ /delete  │ Delete a ticket. Usage: /delete [TICKET_ID]                   │
│ /open    │ Open the current or specified ticket in the default web       │
│          │ browser.                                                      │
│ /comment │ Add a comment to the current ticket. Usage: /comment Your     │
│          │ comment here.                                                 │
│ /rename  │ Rename the summary of the currently focused ticket. Usage:    │
│          │ /rename New summary here.                                     │
│ /ai      │ Enter AI chat mode. Usage: /ai                                │
│ /assign  │ Assign the current ticket or a specified ticket to yourself.  │
│ /new     │ Create a new ticket. If a ticket ID is provided, create a     │
│          │ subtask. Usage: /new [PARENT_TICKET_ID]                       │
│ /tree    │ Display issue tree starting from current or specified ticket. │
└──────────┴───────────────────────────────────────────────────────────────┘
No initial ticket or search string provided. Starting interactive shell.
Type '/help' for help.
Jira>
```

## Configuration

You can customize the CLI behavior by modifying the `.env` file. Available options include:

- `JIRA_URL`: Your Jira instance URL
- `JIRA_USERNAME`: Your Jira username
- `JIRA_API_TOKEN`: Your Jira API token
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: The OpenAI model to use (default: gpt-3.5-turbo)
- `EDITOR`: Your preferred text editor for editing issue descriptions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
