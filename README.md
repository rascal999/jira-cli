# Jira CLI

Jira CLI is an interactive command-line interface for managing Jira issues efficiently. It provides a set of commands to interact with Jira, view and update tickets, manage attachments, and perform various other Jira-related tasks.

## Features

- Interactive shell for Jira operations
- View and update ticket details
- Create new tickets
- Manage attachments
- Perform JQL queries
- View linked issues and child tasks
- AI-powered assistance for Jira tasks

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/jira-cli.git
   cd jira-cli
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   Create a `.env` file in the project root and add the following:
   ```
   JIRA_SERVER=https://your-jira-instance.atlassian.net
   JIRA_EMAIL=your-email@example.com
   JIRA_API_TOKEN=your-jira-api-token
   OPENAI_API_KEY=your-openai-api-key
   ```

## Usage

To start the Jira CLI, run:

```
python main.py
```

Once in the interactive shell, you can use various commands to interact with Jira. Type `help` to see a list of available commands.

## Key Commands

- `vid <TICKET-ID>`: View details of a specific ticket
- `new <PROJECT-ID> <TYPE> <SUMMARY>`: Create a new ticket
- `update`: Update the description of the current ticket
- `comment`: Add a comment to the current ticket
- `attach <FILE>`: Attach a file to the current ticket
- `vct`: View child tasks of the current ticket
- `vli`: View linked issues of the current ticket
- `jql <QUERY>`: Perform a JQL query
- `ai`: Start an AI-powered interactive shell for Jira tasks

## Configuration

The Jira CLI uses a cache system to improve performance. Cache files are stored in the `cache` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
