import logging

from frangilive.audio.interfaces.audio_router import AudioRouterGateway
from frangilive.audio.interfaces.audio_engine import AudioEngineGateway

_logger = logging.getLogger(__name__)


class MockAudioSystem(AudioRouterGateway, AudioEngineGateway):
    def __init__(self):
        self._running = False
        self.connections: set[tuple[str, str]] = set()
        self.connect_calls: list[tuple[str, str]] = []
        self.disconnect_calls: list[tuple[str, str]] = []
        self.remove_all_calls: int = 0

    def start(self, **kwargs) -> None:
        _logger.info(f"Mock: Starting audio engine with options: {kwargs}")
        self._running = True

    def stop(self) -> None:
        _logger.info("Mock: Stopping audio engine")
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def connect(self, source_port_name: str, target_port_name: str) -> None:
        _logger.info(f"Mock: Connecting {source_port_name} to {target_port_name}")
        self.connections.add((source_port_name, target_port_name))
        self.connect_calls.append((source_port_name, target_port_name))

    def disconnect(self, source_port_name: str, target_port_name: str) -> None:
        _logger.info(f"Mock: Disconnecting {source_port_name} from {target_port_name}")
        self.connections.discard((source_port_name, target_port_name))
        self.disconnect_calls.append((source_port_name, target_port_name))

    def remove_all_connections(self) -> None:
        _logger.info("Mock: Removing all connections")
        self.connections.clear()
        self.remove_all_calls += 1
