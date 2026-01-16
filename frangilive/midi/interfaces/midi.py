from abc import ABC, abstractmethod
from typing import Any


class MidiGateway(ABC):
    @abstractmethod
    def open_input(self, name_prefix: str) -> Any:
        pass

    @abstractmethod
    def open_output(self, name_prefix: str) -> Any:
        pass

    @abstractmethod
    def close_all(self) -> None:
        pass
