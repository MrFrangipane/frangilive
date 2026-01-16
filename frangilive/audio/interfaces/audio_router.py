from abc import ABC, abstractmethod


class AudioRouterGateway(ABC):
    @abstractmethod
    def connect(self, source_port_name: str, target_port_name: str) -> None:
        pass

    @abstractmethod
    def disconnect(self, source_port_name: str, target_port_name: str) -> None:
        pass

    @abstractmethod
    def remove_all_connections(self) -> None:
        pass
