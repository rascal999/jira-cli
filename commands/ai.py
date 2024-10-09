from rich.console import Console
import openai
import os
import cmd
from rich.prompt import Confirm, Prompt
from datetime import datetime
import time

console = Console()

class AIChatShell(cmd.Cmd):
    def __init__(self, openai_client, model, issue_manager, current_ticket):
        super().__init__()
        self.openai_client = openai_client
        self.model = model
        self.prompt = f"{model}> "
        self.issue_manager = issue_manager
        self.current_ticket = current_ticket
        self.transcript = []
        self.timezone = time.tzname[0]  # Get the name of the local timezone
        self.user_name = self.get_jira_user_name()

    def get_jira_user_name(self):
        try:
            user = self.issue_manager.jira.myself()
            return user['displayName']  # This should return the full name
        except Exception as e:
            console.print(f"Error fetching Jira user name: {str(e)}", style="red")
            return "User"

    def default(self, line):
        if line.lower() == '/q':
            return True
        timestamp = self.get_formatted_timestamp()
        self.transcript.append(f"[{timestamp}] {self.user_name}: {line}")
        response = ask_ai(self.openai_client, line, self.model)
        self.transcript.append(f"[{timestamp}] {self.model}: {response}")

    def get_formatted_timestamp(self):
        now = time.localtime()
        offset = time.strftime("%z", now)
        return time.strftime("%Y-%m-%d %H:%M:%S %Z", now) + f" ({offset})"

    def do_q(self, arg):
        """Quit the AI chat shell"""
        return True

    def emptyline(self):
        pass

    def save_transcript(self):
        if not self.transcript:
            console.print("No conversation to save.", style="yellow")
            return

        ticket_id = self.current_ticket
        while not ticket_id:
            ticket_id = Prompt.ask("Enter the ticket ID to attach the transcript to").strip()
            if not ticket_id:
                console.print("Ticket ID cannot be empty. Please try again.", style="yellow")

        if Confirm.ask(f"Do you want to save the transcript to ticket {ticket_id}?", default=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"ai_transcript_{timestamp}.txt"
            transcript_text = "\n".join(self.transcript)
            try:
                self.issue_manager.add_attachment(ticket_id, filename, transcript_text)
                console.print(f"Transcript saved to ticket {ticket_id} as {filename}", style="green")
            except ValueError as e:
                console.print(f"Error: {str(e)}", style="red")
                console.print("The transcript was not saved.", style="yellow")
            except Exception as e:
                console.print(f"Unexpected error: Unable to save transcript to ticket {ticket_id}.", style="red")
                console.print("The transcript was not saved.", style="yellow")

def ask_ai(openai_client, question, model):
    try:
        if hasattr(openai, 'OpenAI'):
            # New version of OpenAI library
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": question}
                ]
            )
            ai_response = response.choices[0].message.content
        else:
            # Old version of OpenAI library
            if "gpt-3.5-turbo" in model or "gpt-4" in model:
                # Use chat completions for GPT-3.5-turbo and GPT-4 models
                response = openai_client.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": question}
                    ]
                )
                ai_response = response.choices[0].message.content
            else:
                # Use completions for other models
                response = openai_client.Completion.create(
                    engine=model,
                    prompt=question,
                    max_tokens=150
                )
                ai_response = response.choices[0].text.strip()
        
        console.print(f"AI Response:", style="blue bold")
        console.print(ai_response, style="blue")
        return ai_response
    except Exception as e:
        error_message = f"Error: {str(e)}"
        console.print(error_message, style="red")
        return error_message

def execute(cli, arg):
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not specified
    ai_shell = AIChatShell(cli.openai_client, model, cli.issue_manager, cli.current_ticket)
    console.print(f"Entering AI chat mode with {model}. Type '/q' to quit.", style="green")
    ai_shell.cmdloop()
    ai_shell.save_transcript()

COMMAND = "ai"
HELP = "Enter AI chat mode. Usage: /ai"