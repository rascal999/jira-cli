from rich.console import Console
import openai
import os

console = Console()

def execute(cli, arg):
    ask_ai(cli.openai_client, arg)

def ask_ai(openai_client, question):
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not specified
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
        
        console.print(f"AI Response (using {model}):", style="blue bold")
        console.print(ai_response, style="blue")
    except Exception as e:
        console.print(f"Error: {str(e)}", style="red")

COMMAND = "ai"
HELP = "Ask a question to ChatGPT. Usage: /ai Your question here."