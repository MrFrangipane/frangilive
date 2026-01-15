from dataclasses import dataclass

from frangilive.instrument.audio import AudioInstrument
from frangilive.instrument.audio_port import AudioPort


@dataclass
class AudioConnection:
    source_instrument: AudioInstrument
    source_port: AudioPort
    target_instrument: AudioInstrument
    target_port: AudioPort
