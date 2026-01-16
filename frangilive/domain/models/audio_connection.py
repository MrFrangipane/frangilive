from dataclasses import dataclass
from .audio_instrument import AudioInstrument
from .audio_port import AudioPort


@dataclass(frozen=True)
class AudioConnection:
    source_instrument: AudioInstrument
    source_port: AudioPort
    target_instrument: AudioInstrument
    target_port: AudioPort
