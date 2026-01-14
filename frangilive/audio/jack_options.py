from dataclasses import dataclass

from frangilive.audio.interface_connection_type import InterfaceConnectionType
from frangilive.audio.typing import AudioDriver


@dataclass
class JackOptions:
    buffer_size: int
    driver: AudioDriver
    interface_connection_type: InterfaceConnectionType
