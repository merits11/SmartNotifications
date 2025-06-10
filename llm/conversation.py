from __future__ import annotations

import datetime
import json
import logging
from typing import Union, Dict, List

import tiktoken
from markdown2 import markdown

from utils.config import read_config

encoding = tiktoken.encoding_for_model("gpt-4o")
logger = logging.getLogger(__name__)

MessageContent = Union[str, Dict, List[Union[str, Dict]]]


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

    def add_message(self, role: str, content: MessageContent) -> None:
        # If content is a dict with a "type" key (e.g. image_url), wrap it in a list per OpenAI API requirements
        if isinstance(content, dict) and "type" in content:
            content = [content]
        self.messages.append({"role": role, "content": content})

    def add_user_message(self, content: MessageContent):
        # The add_message method now handles wrapping image block dicts as needed
        self.add_message("user", content)

    def add_assistant_message(self, content: MessageContent):
        self.add_message("assistant", content)

    def add_system_message(self, content: MessageContent) -> None:
        if isinstance(content, list):
            for item in content:
                self.add_system_message(item)
            return
        if self.model and self.model.startswith("o1"):
            self.add_user_message(content)
            return  # No system messages for o1 models
        self.messages.append({"role": "system", "content": content})

    def delete_message(self, index: int) -> None:
        if 0 <= index < len(self.messages):
            self.messages[index]["content"] = "[DELETED]"

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
            "token_usage": self.token_usage,
        }

    def as_inner_html(self, last_n: int = 1):
        markdown_content = ""
        if last_n > len(self.messages):
            last_n = len(self.messages)
        for message in self.messages[-last_n:]:
            markdown_content += (
                f"**{message['role'].upper()}**\n\n{message['content']}\n\n"
            )
        # Convert Markdown to HTML
        return markdown(markdown_content)

    def as_html(self, last_n=1):
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Markdown Output</title>
        </head>
        <body>
            {self.as_inner_html(last_n=last_n)}
        </body>
        </html>
        """
