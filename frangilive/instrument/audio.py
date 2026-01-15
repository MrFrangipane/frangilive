from dataclasses import dataclass, field

from frangilive.instrument.audio_port import AudioPort


@dataclass
class AudioInstrument:
    name: str
    inputs: list[AudioPort] = field(default_factory=list)
    outputs: list[AudioPort] = field(default_factory=list)

    def input(self, name: str) -> tuple[str, AudioPort]:
        for port in self.inputs:
            if port.name == name:
                return self.name, port

        raise ValueError(f"Input port '{name}' not found for '{self.name}'")

    def output(self, name: str) -> tuple[str, AudioPort]:
        for port in self.outputs:
            if port.name == name:
                return self.name, port

        raise ValueError(f"Output port '{name}' not found for '{self.name}'")
