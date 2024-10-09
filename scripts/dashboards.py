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

def get_all_jira_dashboards():
    # Define the endpoint for Jira dashboards API
    url = f"{JIRA_URL}/rest/api/2/dashboard"

    # Set up the headers and authentication
    headers = {
        "Content-Type": "application/json",
    }
    auth = (JIRA_USERNAME, JIRA_API_TOKEN)

    dashboards = []
    start_at = 0
    max_results = 50  # You can adjust this to fetch more results per request if needed

    while True:
        # Make the API request to get dashboards with pagination
        params = {'startAt': start_at, 'maxResults': max_results}
        try:
            response = requests.get(url, headers=headers, auth=auth, params=params)

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                new_dashboards = data.get('dashboards', [])
                dashboards.extend(new_dashboards)

                # Check if we have fetched all dashboards
                if len(new_dashboards) < max_results:
                    break  # No more dashboards to fetch
                start_at += max_results
            else:
                print(f"Failed to fetch dashboards: {response.status_code} - {response.text}")
                break
        except Exception as e:
            print(f"An error occurred while fetching dashboards: {e}")
            break

    return dashboards

def display_dashboards(dashboards):
    # Create a list of dashboard information for tabulation
    dashboard_list = []
    for dashboard in dashboards:
        dashboard_id = dashboard.get('id', 'N/A')
        name = dashboard.get('name', 'N/A')
        owner = dashboard.get('owner', {}).get('displayName', 'N/A')
        view_url = dashboard.get('viewUrl', 'N/A')  # Handle missing 'viewUrl'

        dashboard_list.append([dashboard_id, name, owner, view_url])

    # Print the dashboards in a table format using tabulate
    print(tabulate(dashboard_list, headers=["ID", "Name", "Owner", "URL"], tablefmt="grid"))

if __name__ == "__main__":
    dashboards = get_all_jira_dashboards()
    if dashboards:
        display_dashboards(dashboards)
    else:
        print("No dashboards found or an error occurred.")
