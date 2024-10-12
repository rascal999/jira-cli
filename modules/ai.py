import os
from dotenv import load_dotenv
import openai
from rich.console import Console
from rich.markdown import Markdown
from common.jira_client import get_jira_client
from datetime import datetime
import pytz
from common.utils import confirm_action

# Load environment variables
load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

def run(args, current_ticket=None):
    console = Console()

    if not OPENAI_API_KEY:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY is not set in the .env file.")
        return

    openai.api_key = OPENAI_API_KEY

    console.print("[bold green]Welcome to the AI Interactive Shell![/bold green]")
    console.print(f"Using model: [cyan]{OPENAI_MODEL}[/cyan]")
    console.print("Type 'exit' to quit the AI shell.")

    conversation = []
    transcript = []

    # Get the current user's name
    try:
        jira = get_jira_client()
        current_user = jira.myself()
        user_name = current_user.get('displayName') or current_user.get('name') or current_user.get('emailAddress') or "Unknown User"
    except Exception as e:
        console.print(f"[bold yellow]Warning:[/bold yellow] Unable to fetch current user's name. {str(e)}")
        user_name = "Unknown User"

    # Add initial transcript entry
    transcript.append(f"AI Conversation Transcript\n")
    transcript.append(f"Model: {OPENAI_MODEL}\n")
    transcript.append(f"User: {user_name}\n")
    transcript.append(f"Date: {datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")

    while True:
        user_input = console.input("[bold blue]You:[/bold blue] ")

        if user_input.lower() == 'exit':
            break

        timestamp = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
        transcript.append(f"{timestamp} - You: {user_input}\n")

        conversation.append({"role": "user", "content": user_input})

        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=conversation
            )

            ai_response = response.choices[0].message['content']
            conversation.append({"role": "assistant", "content": ai_response})

            console.print("[bold green]AI:[/bold green]")
            console.print(Markdown(ai_response))

            timestamp = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
            transcript.append(f"{timestamp} - AI: {ai_response}\n")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

    console.print("[bold green]Exiting AI Interactive Shell.[/bold green]")

    if current_ticket:
        if confirm_action("Do you want to save the transcript as an attachment to the current ticket?"):
            try:
                jira = get_jira_client()
                issue = jira.issue(current_ticket)

                # Create a temporary file for the transcript
                temp_file_name = f"ai_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(temp_file_name, 'w') as f:
                    f.writelines(transcript)

                # Attach the file to the Jira ticket
                with open(temp_file_name, 'rb') as f:
                    jira.add_attachment(issue=issue, attachment=f, filename=temp_file_name)

                console.print(f"[bold green]Transcript saved as attachment to {current_ticket}[/bold green]")

                # Remove the temporary file
                os.remove(temp_file_name)

            except Exception as e:
                console.print(f"[bold red]Error saving transcript:[/bold red] {str(e)}")
        else:
            console.print("Transcript not saved.")
    else:
        console.print("No ticket is currently focused. Transcript not saved.")

HELP_TEXT = "Open an interactive shell with OpenAI"
