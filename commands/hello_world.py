from rich.console import Console

console = Console()

def hello_world():
    """Print 'Hello World!' to the console."""
    console.print("Hello World!", style="bold green")

def execute(arg=None):
    """Execute the hello_world command."""
    hello_world()

# Command information
COMMAND = "hello"
HELP = "Print 'Hello World!' to the console"
