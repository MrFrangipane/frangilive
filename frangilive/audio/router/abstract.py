from abc import ABC, abstractmethod

from frangilive.audio.jack_options import JackOptions
from frangilive.patcher.audio_connection_info import AudioConnectionInfo


class AbstractAudioRouter(ABC):

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
    def connect(self, info: AudioConnectionInfo) -> None:
        pass

    @abstractmethod
    def disconnect(self, info: AudioConnectionInfo) -> None:
        pass
