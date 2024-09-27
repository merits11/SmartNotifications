import functools
import os
from openai import OpenAI

from utils.config import read_llm_token


@functools.lru_cache(maxsize=1)
def get_openai_client():
    token = read_llm_token()
    return OpenAI(api_key=token)


@functools.lru_cache(maxsize=1)
def get_llm_client():
    return Client()


class Client:  # pylint: disable=too-few-public-methods

    def __init__(self, model="gpt-4o-mini", client=get_openai_client()) -> None:
        self.client = client
        self.model = model

    def get_chat_completion(self, messages, model=None, tools=None):
        our_model = model if model else self.model
        return self.client.chat.completions.create(model=our_model, messages=messages, tools=tools)
