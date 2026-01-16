import mido
from frangilive.midi.interfaces.midi import MidiGateway


class MidoMidiGateway(MidiGateway):
    def __init__(self):
        self._inputs = []
        self._outputs = []

    def _find_name(self, name_prefix: str, names: list[str]):
        for name in names:
            if name.startswith(name_prefix):
                return name
        raise ValueError(f"No port name starting with '{name_prefix}' found.")

    def open_input(self, name_prefix: str):
        full_name = self._find_name(name_prefix, mido.get_input_names())
        port = mido.open_input(full_name)
        self._inputs.append(port)
        return port

    def open_output(self, name_prefix: str):
        full_name = self._find_name(name_prefix, mido.get_output_names())
        port = mido.open_output(full_name)
        self._outputs.append(port)
        return port

    def close_all(self):
        for port in self._inputs:
            port.close()
        for port in self._outputs:
            port.close()
        self._inputs.clear()
        self._outputs.clear()
