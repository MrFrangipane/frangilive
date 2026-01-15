from dataclasses import dataclass


@dataclass
class AudioConnectionInfo:
    source_instrument: str
    source_port: str
    target_instrument: str
    target_port: str
