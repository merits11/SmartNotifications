import os
from pathlib import Path
from typing import Dict


def read_telegram_config():
    # Build the path to the file using the HOME environment variable
    config_path = Path(os.getenv("HOME")) / ".telegram" / "chat-config"

    # Dictionary to store the token and chat_id
    config = read_config(config_path)

    return config['token'], config['chat_id'], config['important_chat_id']


def read_llm_token():
    # Build the path to the file using the HOME environment variable
    config_path = Path(os.getenv("HOME")) / ".llm" / "api-token"

    # Dictionary to store the token and chat_id
    config = read_config(config_path)

    return config['token']


def read_config(config_path: str) -> Dict:
    # Dictionary to store the token and chat_id
    config = {}

    # Open and read the file
    with open(config_path, 'r') as file:
        for line in file:
            line = line.split("#")[0]  # support comment with #
            if '=' in line:
                # Split each line into key-value pairs (token and chat_id)
                key, value = line.strip().split('=')
                config[key.strip()] = value.strip()

    return config
