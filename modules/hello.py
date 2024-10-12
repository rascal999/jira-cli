from common.utils import print_header

def run(args=None):
    print_header("Greeting Module")
    name = input("Enter your name: ")
    print(f"Hello, {name}!")

HELP_TEXT = "Greet the user"