#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables from .env file
load_dotenv()

JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

def get_ticket_count(jql_query):
    # Define the endpoint for JIRA search API
    url = f"{JIRA_URL}/rest/api/2/search"

    # Set up the headers and authentication
    headers = {
        "Content-Type": "application/json",
    }
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)

    # Define the request payload
    payload = {
        "jql": jql_query,
        "maxResults": 0,  # We only need the count, no tickets need to be fetched
        "fields": []
    }

    try:
        # Make the API request
        response = requests.post(url, json=payload, headers=headers, auth=auth)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            # Return the total number of tickets found
            return data['total']
        else:
            print(f"Failed to fetch tickets for query '{jql_query}': {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred for query '{jql_query}': {e}")
        return None

def process_jql_file(file_path):
    results = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            i = 0
            while i < len(lines):
                title_line = lines[i].strip()

                # Check if title line starts with #
                if not title_line.startswith('#'):
                    print(f"Error: Expected a comment line starting with '#' at line {i+1}.")
                    return

                # Get the actual title (strip leading # and spaces)
                title = title_line.lstrip('#').strip()

                # Move to the next line for JQL
                i += 1
                if i >= len(lines):
                    print(f"Error: Missing JQL query for the title '{title}'.")
                    return

                jql_query = lines[i].strip()
                if not jql_query:
                    print(f"Error: Empty JQL query provided for the title '{title}' at line {i+1}.")
                    return

                # Fetch the ticket count
                ticket_count = get_ticket_count(jql_query)
                if ticket_count is not None:
                    results.append([title, ticket_count])

                # Move to the next pair of title and JQL
                i += 1

        # Print the results in a table format using tabulate
        if results:
            print(tabulate(results, headers=["Metric", "Count"], tablefmt="grid"))

    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")

if __name__ == "__main__":
    # Specify the path to the JQL file
    jql_file_path = 'jql_queries.txt'
    process_jql_file(jql_file_path)
