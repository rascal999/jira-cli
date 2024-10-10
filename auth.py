import os
import logging
from jira import JIRA
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_jira_client():
    jira_url = os.getenv('JIRA_URL')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_api_token = os.getenv('JIRA_API_TOKEN')
    debug_mode = os.getenv('DEBUG', '0') == '1'

    if not all([jira_url, jira_username, jira_api_token]):
        raise ValueError("Jira credentials are not fully set in the environment variables.")

    options = {'server': jira_url}
    
    if debug_mode:
        #log_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_debug.log"
        log_filename = f"debug.log"
        logging.basicConfig(filename=log_filename, level=logging.DEBUG)
        options['verbose'] = True
        options['logging'] = True

    jira = JIRA(options, basic_auth=(jira_username, jira_api_token))
    return jira
