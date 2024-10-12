import os

def print_header(text):
    print("=" * 40)
    print(text.center(40))
    print("=" * 40)

def confirm_action(prompt):
    while True:
        response = input(f"{prompt} (y/n): ").lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
