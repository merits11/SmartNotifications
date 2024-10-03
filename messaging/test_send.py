import asyncio
import logging

import requests

from messaging.telegram_messenger import TelegramMessenger
from utils.config import read_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [PID:%(process)d][%(threadName)s] - %(message)s",
)


async def main():
    config = read_config()
    token, chat_id, chat_id_2 = config.telegram_token, config.chat_id, config.important_chat_id

    # Create a TelegramMessenger instance
    telegram_messenger = TelegramMessenger(token=token, chat_id=chat_id, important_chat_id=chat_id_2)

    updates_url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(updates_url)
    logging.info(f"getUpdates response: {response.json()}")

    # Use it to send a message
    await telegram_messenger.send_message("Hello from the OOP-based Telegram Messenger!")

    await telegram_messenger.send_important_message("Hello from the OOP-based Telegram Messenger!")


if __name__ == "__main__":
    asyncio.run(main())
