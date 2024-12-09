import datetime
import json

import tiktoken

from utils.config import read_config

encoding = tiktoken.encoding_for_model("gpt-4o")


class Conversation:
    def __init__(self, model=None):
        self.messages = []
        if model:
            self.model = model
        else:
            config = read_config()
            self.model = config.model
        self.token_usage = 0
        self.extra_data = {}
        self.started_at = datetime.datetime.now()

    def add_message(self, role, content: str | list[str]) -> None:
        if isinstance(content, list):
            for item in content:
                self.add_message(role, item)
            return
        self.messages.append({"role": role, "content": content})

    def add_user_message(self, content: str | list[str]):
        self.add_message("user", content)

    def add_assistant_message(self, content: str | list[str]):
        self.add_message("assistant", content)

    def add_system_message(self, content: str | list[str]) -> None:
        if isinstance(content, list):
            for item in content:
                self.add_system_message(item)
            return
        if self.model and self.model.startswith("o1"):
            self.add_user_message(content)
            return  # No system messages for o1 models
        self.messages.append({"role": "system", "content": content})

    def get_conversation(self):
        return self.messages

    def add_metadata(self, key, value):
        self.extra_data[key] = value

    def get_metadata(self, key):
        return self.extra_data.get(key)

    def get_token_usage(self):
        return self.token_usage

    def estimate_token_usage(self):
        self.token_usage = len(encoding.encode(json.dumps(self.to_dict())))

    def to_dict(self):
        return {
            "started_at": self.started_at.isoformat(),
            "model": self.model,
            "messages": self.messages,
            "token_usage": self.token_usage
        }
