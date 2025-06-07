import functools
import os
from pathlib import Path
from typing import Dict

DEFAULT_PROFILE = "default"

GLOBAL_VERBOSE = os.getenv("GLOBAL_VERBOSE", "0") == "1"


class SmartConfig:
    current_profile = DEFAULT_PROFILE

    def __init__(self, config={}):
        self.profiles = {}
        for profile, profile_dict in config.items():
            self.profiles[profile] = profile_dict
        self.apply_profile(SmartConfig.current_profile)

    @staticmethod
    def get_current_profile() -> str:
        return SmartConfig.current_profile

    def apply_profile(self, profile: str):
        self.__apply_profile(DEFAULT_PROFILE, applied_profiles=set([]))
        if profile != DEFAULT_PROFILE:
            self.__apply_profile(profile, applied_profiles=set([]))
        SmartConfig.current_profile = profile

    def __apply_profile(self, profile: str, applied_profiles):
        if profile not in self.profiles:
            raise ValueError(f"Profile {profile} not found")
        if profile in applied_profiles:
            return
        applied_profiles.add(profile)

        attributes = [
            'client', 'model', 'base_url',
            'portkey_api_key', 'portkey_virtual_key',
            'llm_token',
            'telegram_token', 'telegram_chat_id', 'telegram_important_chat_id',
        ]
        for key, value in self.profiles[profile].items():
            if key in attributes:
                setattr(self, key, value)

        # Must apply the referenced profile last
        ref_profile_key = 'use_profile'
        if ref_profile_key in self.profiles[profile]:
            self.__apply_profile(self.profiles[profile][ref_profile_key], applied_profiles=applied_profiles)

    @classmethod
    def from_file(cls, config_path: Path) -> 'SmartConfig':
        config = cls.read_file_config(config_path)
        return cls(config)

    @staticmethod
    def read_file_config(config_path: Path) -> Dict:
        config = {}
        profile = DEFAULT_PROFILE
        profile_config = {}
        config[profile] = profile_config
        with open(config_path, 'r') as file:
            for line in file:
                line = line.split("#")[0].strip()  # support comment with #
                if line.startswith("[") and line.endswith("]"):
                    profile = line[1:-1].strip()
                    profile_config = {}
                    config[profile] = profile_config
                    continue
                if '=' in line:
                    key, value = line.strip().split('=')
                    profile_config[key.strip()] = value.strip()
        return config


@functools.lru_cache(maxsize=1)
def read_config() -> SmartConfig:
    config_path = Path(os.getenv("HOME")) / ".smart" / "config"
    return SmartConfig.from_file(config_path)
