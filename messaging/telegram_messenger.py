import os
from pathlib import Path

from telegram import Bot

from messaging.messenger import Messenger


class TelegramMessenger(Messenger):
    def __init__(self, token: str, chat_id: str, important_chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.important_chat_id = important_chat_id
        self.bot = Bot(token=token)

    async def send_message(self, message: str):
        await self.bot.send_message(chat_id=self.chat_id, text=message)

    async def send_important_message(self, message: str):
        await self.bot.send_message(chat_id=self.important_chat_id, text=message)


def read_telegram_config():
    # Build the path to the file using the HOME environment variable
    config_path = Path(os.getenv("HOME")) / ".telegram" / "chat-config"

    # Dictionary to store the token and chat_id
    config = {}

    # Open and read the file
    with open(config_path, 'r') as file:
        for line in file:
            # Split each line into key-value pairs (token and chat_id)
            key, value = line.strip().split('=')
            config[key] = value

    return config['token'], config['chat_id'], config['important_chat_id']
