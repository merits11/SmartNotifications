class Conversation:
    def __init__(self, model=None):
        self.messages = []
        self.model = model

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_system_message(self, content):
        self.messages.append({"role": "system", "content": content})

    def get_conversation(self):
        return self.messages
