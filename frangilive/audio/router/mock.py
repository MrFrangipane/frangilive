import logging

from frangilive.audio.audio_interface import AudioInterface
from frangilive.audio.jack_options import JackOptions
from frangilive.audio.port import AudioPort
from frangilive.audio.router.abstract import AbstractAudioRouter


_logger = logging.getLogger(__name__)


class MockAudioRouter(AbstractAudioRouter):

    def __init__(self):
        self._audio_interface = AudioInterface("MockAudio", "MockAudio")

    def find_audio_interface(self, name: str) -> bool:
        _logger.info(f"Interface detection")
        return True

    def start_jack_server(self, options: JackOptions):
        _logger.info("JACK server")

    def start_overwitch(self):
        _logger.info("Overwitch")

    def activate_jack_client(self):
        _logger.info("JACK client")

    def remove_all_audio_connections(self):
        _logger.info("Disconnecting all")

    def connect(self, input_info: tuple[str, AudioPort], output_info: tuple[str, AudioPort]) -> None:
        input_instrument_name, input_port = input_info
        output_instrument_name, output_port = output_info
        _logger.info(f"Connecting {input_instrument_name}.{input_port.name} -> {output_instrument_name}.{output_port.name} ({input_port.left} -> {output_port.left})")
