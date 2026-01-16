import logging

from frangilive.audio.interfaces.audio_router import AudioRouterGateway
from frangilive.audio.interfaces.audio_engine import AudioEngineGateway

_logger = logging.getLogger(__name__)


class MockAudioSystem(AudioRouterGateway, AudioEngineGateway):
    def __init__(self):
        self._running = False

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

    def disconnect(self, source_port_name: str, target_port_name: str) -> None:
        _logger.info(f"Mock: Disconnecting {source_port_name} from {target_port_name}")

    def remove_all_connections(self) -> None:
        _logger.info("Mock: Removing all connections")
