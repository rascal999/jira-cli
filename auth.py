import os
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

def get_jira_client():
    jira_url = os.getenv('JIRA_URL')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_api_token = os.getenv('JIRA_API_TOKEN')

    if not all([jira_url, jira_username, jira_api_token]):
        raise ValueError("Jira credentials are not fully set in the environment variables.")

    options = {'server': jira_url}
    jira = JIRA(options, basic_auth=(jira_username, jira_api_token))
    return jira
