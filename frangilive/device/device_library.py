from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

from frangilive.audio.instrument import AudioInstrument


@dataclass_json
@dataclass
class DeviceLibrary:
    name: str
    audio_instruments: list[AudioInstrument] = field(default_factory=list)

    def __post_init__(self):
        self._audio_instruments_index = {instrument.name: instrument for instrument in self.audio_instruments}

    def audio_instrument(self, name: str) -> AudioInstrument | None:
        return self._audio_instruments_index.get(name)
