def quit_program():
    print("Exiting Jira CLI. Goodbye!")
    return True

COMMAND = "quit"
HELP = "Quit the program."

def execute(cli, arg=None):
    return quit_program()
