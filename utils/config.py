import functools
import os
from pathlib import Path
from typing import Dict


class SmartConfig:
    def __init__(self, config=None):
        self.config = config if config else {}
        self.llm_token = self.config.get('llm_token')
        self.telegram_token = self.config.get('telegram_token')
        self.chat_id = self.config.get('telegram_chat_id')
        self.important_chat_id = self.config.get('telegram_important_chat_id')
        self.model = self.config.get('model')
        self.client = self.config.get('client')
        self.base_url = self.config.get('base_url')
        # Portkey:
        self.portkey_api_key = self.config.get('portkey_api_key')
        self.portkey_virtual_key = self.config.get('portkey_virtual_key')

    @classmethod
    def from_file(cls, config_path: Path) -> 'SmartConfig':
        config = cls.read_file_config(config_path)
        return cls(config)

    @staticmethod
    def read_file_config(config_path: Path) -> Dict:
        config = {}
        with open(config_path, 'r') as file:
            for line in file:
                line = line.split("#")[0]  # support comment with #
                if '=' in line:
                    key, value = line.strip().split('=')
                    config[key.strip()] = value.strip()
        return config


@functools.lru_cache(maxsize=1)
def read_config() -> SmartConfig:
    config_path = Path(os.getenv("HOME")) / ".smart" / "config"
    return SmartConfig.from_file(config_path)
