from abc import ABC, abstractmethod


class AudioRouterGateway(ABC):
    def configure_ports(self, device_library) -> None:
        pass

    @abstractmethod
    def set_connections(self, routes: list[tuple[str, str]]) -> None:
        pass

    @abstractmethod
    def connect(self, source_port_name: str, target_port_name: str) -> None:
        pass

    @abstractmethod
    def disconnect(self, source_port_name: str, target_port_name: str) -> None:
        pass

    @abstractmethod
    def remove_all_connections(self) -> None:
        pass
