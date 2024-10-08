class StateManager:
    def __init__(self):
        self.last_viewed_issue = None

    def set_last_viewed_issue(self, issue):
        self.last_viewed_issue = issue

    def get_last_viewed_issue(self):
        return self.last_viewed_issue
