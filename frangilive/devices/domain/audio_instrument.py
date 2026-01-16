from dataclasses import dataclass, field
from .audio_port import AudioPort


@dataclass(frozen=True)
class AudioInstrument:
    name: str
    inputs: list[AudioPort] = field(default_factory=list)
    outputs: list[AudioPort] = field(default_factory=list)

    def get_input(self, name: str) -> AudioPort:
        for port in self.inputs:
            if port.name == name:
                return port
        raise ValueError(f"Input port '{name}' not found for '{self.name}'")

    def get_output(self, name: str) -> AudioPort:
        for port in self.outputs:
            if port.name == name:
                return port
        raise ValueError(f"Output port '{name}' not found for '{self.name}'")
