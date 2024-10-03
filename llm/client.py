import functools

from openai import OpenAI

from llm.conversation import Conversation
from utils.config import read_llm_token

DEFAULT_MODEL = "gpt-4o-mini"


@functools.lru_cache(maxsize=1)
def get_openai_client():
    token = read_llm_token()
    return OpenAI(api_key=token)


@functools.lru_cache(maxsize=1)
def get_llm_client():
    return Client()


class Client:  # pylint: disable=too-few-public-methods

    def __init__(self, model=DEFAULT_MODEL, client=get_openai_client()) -> None:
        self.client = client
        self.model = model

    def get_chat_completion(self, messages, model=None, tools=None):
        our_model = model if model else self.model
        return self.client.chat.completions.create(model=our_model, messages=messages, tools=tools)

    def converse(self, conversation: Conversation, tools=None):
        our_model = conversation.model if conversation.model else self.model
        response = self.client.chat.completions.create(model=our_model, messages=conversation.messages, tools=tools)
        message = response.choices[0].message
        conversation.add_message(message.role, message.content)
        return response
