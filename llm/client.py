import functools
import logging
import json

from openai import OpenAI
from portkey_ai import Portkey

from llm.conversation import Conversation
from utils.config import read_config, GLOBAL_VERBOSE

DEFAULT_MODEL = "gpt-4o-mini"

logger = logging.getLogger(__name__)


def _get_openai_client(config):
    return OpenAI(
        api_key=config.llm_token,
        base_url=config.base_url or "https://api.openai.com/v1",
    )


def _get_portkey_client(config):
    return Portkey(
        base_url=config.base_url,
        api_key=config.portkey_api_key,
        virtual_key=config.portkey_virtual_key,
    )


@functools.lru_cache(maxsize=1)
def get_llm_client():
    config = read_config()
    if config.client == "portkey":
        return Client(client=_get_portkey_client(config))
    else:
        return Client(client=_get_openai_client(config))


def apply_profile(profile):
    config = read_config()
    if profile not in config.profiles:
        return False
    config.apply_profile(profile)
    get_llm_client().reset_client(get_underlying_client(config))
    return True


def get_underlying_client(config):
    if config.client == "portkey":
        return _get_portkey_client(config)
    else:
        return _get_openai_client(config)


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors."""

    pass


class Client:

    def __init__(self, model=None, client=None) -> None:
        self.client = client
        self.model = model if model else DEFAULT_MODEL

    def _call_chat_completion(self, model, messages, tools):
        # debug the messages being sent
        if GLOBAL_VERBOSE:
            logger.info(f"Request to API: {json.dumps(messages, indent=2)}")
        response = self.client.chat.completions.create(
            model=model, messages=messages, tools=tools
        )

        if "error" in response:
            raise OpenAIAPIError(
                f"Error from OpenAI API: {response['error']['message']}"
            )

        return response

    def reset_client(self, new_client):
        self.client = new_client

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

        if GLOBAL_VERBOSE:
            logger.info(f"Streaming to API: {json.dumps(conversation.messages, indent=2)}")

        stream = self.client.chat.completions.create(
            model=our_model,
            messages=conversation.messages,
            tools=tools,
            stream=True,  # Enable streaming
        )

        response_text = ""
        for chunk in stream:
            if "error" in chunk:
                raise OpenAIAPIError(
                    f"Error from OpenAI API: {chunk['error']['message']}"
                )

            if (
                chunk.choices
                and chunk.choices[0].delta
                and chunk.choices[0].delta.content
            ):
                response_text += str(chunk.choices[0].delta.content)
                yield chunk.choices[0].delta
        conversation.add_assistant_message(response_text)
        conversation.estimate_token_usage()
