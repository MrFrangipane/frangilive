from dataclasses import dataclass, field
from .audio_port import AudioPort


@dataclass
class AudioInstrument:
    name: str
    inputs: list[AudioPort] = field(default_factory=list)
    outputs: list[AudioPort] = field(default_factory=list)
    default_input_name: str | None = None
    default_output_name: str | None = None

    def _get_port(self, ports: list[AudioPort], name: str, port_type: str) -> AudioPort:
        for port in ports:
            if port.name == name:
                return port
        raise ValueError(f"{port_type.capitalize()} port '{name}' not found for '{self.name}'")

    def _get_default_port(
            self,
            ports: list[AudioPort],
            default_name: str | None,
            port_type: str,
    ) -> AudioPort | None:
        if default_name:
            return self._get_port(ports, default_name, port_type)
        if ports:
            return ports[0]
        return None

    def get_input(self, name: str) -> AudioPort:
        return self._get_port(self.inputs, name, "input")

    def get_output(self, name: str) -> AudioPort:
        return self._get_port(self.outputs, name, "output")

    def get_default_input(self) -> AudioPort | None:
        return self._get_default_port(self.inputs, self.default_input_name, 'default input')

    def get_default_output(self) -> AudioPort | None:
        return self._get_default_port(self.outputs, self.default_output_name, 'default output')

    def set_default_input(self, name: str) -> None:
        self.get_input(name)
        self.default_input_name = name

    def set_default_output(self, name: str) -> None:
        self.get_output(name)
        self.default_output_name = name
