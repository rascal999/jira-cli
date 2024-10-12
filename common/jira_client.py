import os
from dotenv import load_dotenv
from jira import JIRA

# Load environment variables
load_dotenv()

# Jira configuration
JIRA_SERVER = os.getenv('JIRA_SERVER')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

def get_jira_client():
    if not all([JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise ValueError("Jira configuration is missing. Please check your .env file.")
    
    return JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))

