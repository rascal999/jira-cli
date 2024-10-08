from rich.console import Console

console = Console()

def ask_ai(ai_integration, question):
    response = ai_integration.ask_question(question)
    console.print(f"AI Response: {response}", style="blue")
