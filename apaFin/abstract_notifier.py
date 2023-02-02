from abc import ABC, abstractmethod


class Notifier(ABC):

    @abstractmethod
    def notify(self, message: str):
        """Notify users with the given message"""
        pass
