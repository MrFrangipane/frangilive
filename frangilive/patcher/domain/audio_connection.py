from dataclasses import dataclass
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.domain.audio_port import AudioPort


@dataclass(frozen=True)
class AudioConnection:
    source_instrument: AudioInstrument
    source_port: AudioPort
    target_instrument: AudioInstrument
    target_port: AudioPort
