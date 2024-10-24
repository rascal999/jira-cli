import os

def print_header(text):
    print("=" * 40)
    print(text.center(40))
    print("=" * 40)

def confirm_action(prompt, default=False):
    default_str = "y" if default else "n"
    while True:
        response = input(f"{prompt} (y/n) [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
