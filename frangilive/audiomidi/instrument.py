from dataclasses import dataclass, field

from frangilive.audiomidi.audio_port import AudioPort


@dataclass
class Instrument:
    name: str
    inputs: list[AudioPort] = field(default_factory=list)
    outputs: list[AudioPort] = field(default_factory=list)

    def input(self, name: str) -> AudioPort:
        for port in self.inputs:
            if port.name == name:
                return port

        raise ValueError(f"Input port '{name}' not found in {self.name}")

    def output(self, name: str):
        for port in self.outputs:
            if port.name == name:
                return port

        raise ValueError(f"Output port '{name}' not found in {self.name}")
