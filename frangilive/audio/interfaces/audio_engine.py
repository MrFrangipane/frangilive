from abc import ABC, abstractmethod


class AudioEngineGateway(ABC):
    @abstractmethod
    def start(self, **kwargs) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def is_running(self) -> bool:
        pass
