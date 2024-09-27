from abc import ABC, abstractmethod


class Messenger(ABC):
    @abstractmethod
    def send_message(self, message: str):
        pass

    @abstractmethod
    def send_important_message(self, message: str):
        pass
