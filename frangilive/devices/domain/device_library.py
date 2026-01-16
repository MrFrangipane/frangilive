from dataclasses import dataclass, field
from .audio_instrument import AudioInstrument


@dataclass
class DeviceLibrary:
    name: str
    audio_instruments: list[AudioInstrument] = field(default_factory=list)

    def __post_init__(self):
        self._audio_instruments_index = {instrument.name: instrument for instrument in self.audio_instruments}

    def get_instrument(self, name: str) -> AudioInstrument | None:
        return self._audio_instruments_index.get(name)

    @property
    def instruments_with_output(self) -> list[AudioInstrument]:
        return [i for i in self.audio_instruments if i.outputs]

    @property
    def instruments_with_input(self) -> list[AudioInstrument]:
        return [i for i in self.audio_instruments if i.inputs]
