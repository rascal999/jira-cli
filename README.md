# jira-cli
Jira from the CLI

```
❯ ./jira_cli_1.py

Available Commands:

/h           - Show this help message.
/q           - Quit the program.
/c           - Add a comment to the last ticket. Usage: /c Your comment here.
/s           - Enter JQL mode to execute a JQL query.
/d TICKET    - Delete a ticket. Usage: /d TICKET_ID
/r           - Display top 10 recently updated tickets reported by you.
/t [TICKET]  - Display issue tree starting from current or specified ticket.
/n           - Create a new ticket under the current ticket (epic or task), or create a new epic if no ticket is
focused.
/l TICKET    - Link current ticket to specified ticket as 'Relates to'.
/e           - List all epics reported by you.
/x           - Clear the current focused ticket.
/u           - Update the description of the currently focused ticket.
/p           - Change focus to parent ticket and display its details.
/i           - Ask a question to ChatGPT. Usage: /i Your question here.
/a <summary> - Rename the summary of the currently focused ticket. Usage: /a New summary here.

Type a ticket ID or search string to display ticket information or search results.

When a ticket is focused, press [Tab] to display possible statuses above the prompt. Type the status name and
press [Enter] to update the ticket to the selected status.

No initial ticket or search string provided. Starting interactive shell.

Type '/h' for help.
>
```

## Install

```
cp .env-example .env
```

Update .env

```
pip install prompt_toolkit python-dotenv jira rich openai
```
