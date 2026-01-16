from dataclasses import dataclass, field
from .audio_connection import AudioConnection
from frangilive.devices.domain.device_library import DeviceLibrary


@dataclass
class Patcher:
    device_library: DeviceLibrary
    connections: list[AudioConnection] = field(default_factory=list)

    def add_connection(self, connection: AudioConnection):
        if connection not in self.connections:
            self.connections.append(connection)

    def remove_connection(self, connection: AudioConnection):
        if connection in self.connections:
            self.connections.remove(connection)

    def get_connections_between(self, source_name: str, target_name: str) -> list[AudioConnection]:
        return [
            c for c in self.connections
            if c.source_instrument.name == source_name and c.target_instrument.name == target_name
        ]
