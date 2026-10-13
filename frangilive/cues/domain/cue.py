from dataclasses import dataclass, field
from frangilive.patcher.domain.audio_connection import AudioConnection


@dataclass
class Cue:
    """
    A Cue represents a snapshot of live performance state (audio patcher connections,
    and in future extensions, MIDI program changes and device states).
    """
    name: str
    connections: list[AudioConnection] = field(default_factory=list)

    def __post_init__(self):
        # Store a shallow copy list of connections to prevent accidental external mutation
        self.connections = list(self.connections)

    def set_connections(self, connections: list[AudioConnection]) -> None:
        self.connections = list(connections)

    def connection_count(self) -> int:
        return len(self.connections)
