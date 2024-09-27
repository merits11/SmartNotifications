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
