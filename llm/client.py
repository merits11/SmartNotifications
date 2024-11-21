import functools

from openai import OpenAI

from llm.conversation import Conversation
from utils.config import read_config

DEFAULT_MODEL = "gpt-4o-mini"


@functools.lru_cache(maxsize=1)
def get_openai_client():
    config = read_config()
    return OpenAI(api_key=config.llm_token)


@functools.lru_cache(maxsize=1)
def get_llm_client():
    return Client()


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors."""
    pass


class Client:

    def __init__(self, model=None, client=get_openai_client()) -> None:
        self.client = client
        self.model = model if model else DEFAULT_MODEL

    def _call_chat_completion(self, model, messages, tools):
        response = self.client.chat.completions.create(model=model, messages=messages, tools=tools)

        if 'error' in response:
            raise OpenAIAPIError(f"Error from OpenAI API: {response['error']['message']}")

        return response

    def get_chat_completion(self, messages, model=None, tools=None):
        our_model = model if model else self.model
        return self._call_chat_completion(our_model, messages, tools)

    def converse(self, conversation: Conversation, tools=None):
        our_model = conversation.model if conversation.model else self.model
        response = self._call_chat_completion(our_model, conversation.messages, tools)

        message = response.choices[0].message
        conversation.add_message(message.role, message.content)
        # Log the total token usage
        conversation.token_usage = response.usage.total_tokens
        return response

    # New streaming method
    def converse_stream(self, conversation: Conversation, tools=None):
        """
        This method streams the response from the LLM as it is generated.

        Yields:
            Each chunk of the response as it becomes available.
        """
        our_model = conversation.model if conversation.model else self.model
        stream = self.client.chat.completions.create(
            model=our_model,
            messages=conversation.messages,
            tools=tools,
            stream=True  # Enable streaming
        )

        response_text = ""
        for chunk in stream:
            if 'error' in chunk:
                raise OpenAIAPIError(f"Error from OpenAI API: {chunk['error']['message']}")

            if chunk.choices and chunk.choices[0].delta:
                response_text += str(chunk.choices[0].delta.content)
                yield chunk.choices[0].delta
        conversation.add_message("assistant", response_text)
        conversation.estimate_token_usage()
