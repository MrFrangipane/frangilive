from importlib.resources import files

from frangilive import resources
from frangilive.device.device_library import DeviceLibrary
from frangilive.instrument.audio import AudioInstrument
from frangilive.patcher.audio_connection import AudioConnection
from frangilive.patcher.audio_connection_info import AudioConnectionInfo


class Patcher:
    def __init__(self):
        self._audio_instruments: list[AudioInstrument] = []
        self._instruments_with_output: list[AudioInstrument] = []
        self._instruments_with_input: list[AudioInstrument] = []

        self._connections: list[AudioConnection] = []

        # FIXME create a DeviceLibraryStore class
        filepath = files(resources).joinpath("devices.json")
        self._device_library: DeviceLibrary = DeviceLibrary.from_json(open(filepath).read())
        self.set_audio_instruments(self._device_library.audio_instruments)

    def audio_instrument(self, name: str) -> AudioInstrument | None:
        return self._device_library.audio_instrument(name)

    def all_instruments(self) -> list[AudioInstrument]:
        return self._audio_instruments

    def instrument_count(self) -> int:
        return len(self._audio_instruments)

    def set_audio_instruments(self, audio_instruments: list[AudioInstrument]):
        self._audio_instruments = audio_instruments
        self._instruments_with_output.clear()
        self._instruments_with_input.clear()

        for instrument in audio_instruments:
            if instrument.outputs:
                self._instruments_with_output.append(instrument)
            if instrument.inputs:
                self._instruments_with_input.append(instrument)

    def connect(self, connection_info: AudioConnectionInfo) -> bool:
        source_instrument = self.audio_instrument(connection_info.source_instrument)
        target_instrument = self.audio_instrument(connection_info.target_instrument)
        connection = AudioConnection(
            source_instrument=source_instrument,
            source_port=source_instrument.output(connection_info.source_port)[1],
            target_instrument=target_instrument,
            target_port=target_instrument.input(connection_info.target_port)[1]
        )
        if connection not in self._connections:
            self._connections.append(connection)
            return True

        return False

    def disconnect(self, connection_info: AudioConnectionInfo) -> bool:
        source_instrument = self.audio_instrument(connection_info.source_instrument)
        target_instrument = self.audio_instrument(connection_info.target_instrument)
        connection = AudioConnection(
            source_instrument=source_instrument,
            source_port=source_instrument.output(connection_info.source_port)[1],
            target_instrument=target_instrument,
            target_port=target_instrument.input(connection_info.target_port)[1]
        )
        if connection in self._connections:
            self._connections.remove(connection)
            return True

        return False

    def connections_for_instrument_out(self, instrument: AudioInstrument) -> list[AudioConnection]:
        return [connection for connection in self._connections if connection.source_instrument == instrument]

    def connections_for_instrument_in(self, instrument: AudioInstrument) -> list[AudioConnection]:
        return [connection for connection in self._connections if connection.target_instrument == instrument]

    def connections_between_instruments(self, source: AudioInstrument, target: AudioInstrument) -> list[AudioConnection]:
        return [
            connection for connection in self._connections
            if connection.source_instrument == source and connection.target_instrument == target
        ]
