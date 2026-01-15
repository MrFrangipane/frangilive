import logging

from frangilive.audio.audio_interface import AudioInterface
from frangilive.audio.jack_options import JackOptions
from frangilive.audio.router.abstract import AbstractAudioRouter
from frangilive.patcher.audio_connection_info import AudioConnectionInfo

_logger = logging.getLogger(__name__)


class MockAudioRouter(AbstractAudioRouter):

    def __init__(self):
        self._audio_interface = AudioInterface("MockAudio", "MockAudio")

    def find_audio_interface(self, name: str) -> bool:
        _logger.info(f"Interface detection for '{name}'")
        return True

    def start_jack_server(self, options: JackOptions):
        _logger.info(f"JACK server: {options}")

    def start_overwitch(self):
        _logger.info("Overwitch")

    def activate_jack_client(self):
        _logger.info("JACK client")

    def remove_all_audio_connections(self):
        _logger.info("Disconnecting all")

    def disconnect(self, info: AudioConnectionInfo) -> None:
        _logger.info(f"Disconnecting {info.source_instrument}.{info.source_port} -> {info.target_instrument}.{info.target_port}")

    def connect(self, info: AudioConnectionInfo) -> None:
        _logger.info(f"Connecting {info.source_instrument}.{info.source_port} -> {info.target_instrument}.{info.target_port}")
