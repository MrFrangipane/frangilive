from abc import ABC, abstractmethod

from frangilive.audiomidi.audio_port import AudioPort
from frangilive.audiomidi.jack_options import JackOptions


class AbstractAudioMidi(ABC):

    @abstractmethod
    def find_audio_interface(self, name: str) -> bool:
        pass

    @abstractmethod
    def start_jack_server(self, options: JackOptions):
        pass

    @abstractmethod
    def start_overwitch(self):
        pass

    @abstractmethod
    def activate_jack_client(self):
        pass

    @abstractmethod
    def remove_all_audio_connections(self):
        pass

    @abstractmethod
    def connect(self, input_port: AudioPort, output_port: AudioPort) -> None:
        pass
