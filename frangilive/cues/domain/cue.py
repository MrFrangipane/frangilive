from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from frangilive.devices.domain.device_library import DeviceLibrary

from frangilive.patcher.domain.audio_connection import AudioConnection, AudioConnectionSnapshot


@dataclass(frozen=True)
class CueSnapshot:
    """Fully immutable snapshot representing a cue's persistent state."""
    name: str
    connections: tuple[AudioConnectionSnapshot, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "connections": [conn.to_dict() for conn in self.connections],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CueSnapshot:
        return cls(
            name=data["name"],
            connections=tuple(
                AudioConnectionSnapshot.from_dict(c) for c in data.get("connections", [])
            ),
        )

    def to_cue(self, library: DeviceLibrary) -> Cue:
        return Cue.from_snapshot(self, library)


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

    def to_snapshot(self) -> CueSnapshot:
        return CueSnapshot(
            name=self.name,
            connections=tuple(conn.to_snapshot() for conn in self.connections),
        )

    @classmethod
    def from_snapshot(cls, snapshot: CueSnapshot, library: DeviceLibrary) -> Cue:
        connections = [
            AudioConnection.from_snapshot(cs, library)
            for cs in snapshot.connections
        ]
        return cls(name=snapshot.name, connections=connections)
