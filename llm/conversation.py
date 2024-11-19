class Conversation:
    def __init__(self, model=None):
        self.messages = []
        self.model = model
        self.token_usage = 0
        self.extra_data = {}

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_system_message(self, content):
        self.messages.append({"role": "system", "content": content})

    def get_conversation(self):
        return self.messages

    def add_metadata(self, key, value):
        self.extra_data[key] = value

    def get_metadata(self, key):
        return self.extra_data.get(key)

    def to_dict(self):
        return {
            "model": self.model,
            "messages": self.messages,
            "token_usage": self.token_usage
        }
