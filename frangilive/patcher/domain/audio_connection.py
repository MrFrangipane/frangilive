from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from frangilive.devices.domain.device_library import DeviceLibrary

from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.domain.audio_port import AudioPort


@dataclass(frozen=True)
class AudioConnectionSnapshot:
    """Lightweight, fully immutable value object capturing a single connection."""
    source_instrument: str
    source_port: str
    target_instrument: str
    target_port: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source_instrument": self.source_instrument,
            "source_port": self.source_port,
            "target_instrument": self.target_instrument,
            "target_port": self.target_port,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AudioConnectionSnapshot:
        return cls(
            source_instrument=data["source_instrument"],
            source_port=data["source_port"],
            target_instrument=data["target_instrument"],
            target_port=data["target_port"],
        )

    def to_connection(self, library: DeviceLibrary) -> AudioConnection:
        return AudioConnection.from_snapshot(self, library)


@dataclass(frozen=True)
class AudioConnection:
    source_instrument: AudioInstrument
    source_port: AudioPort
    target_instrument: AudioInstrument
    target_port: AudioPort

    def to_snapshot(self) -> AudioConnectionSnapshot:
        return AudioConnectionSnapshot(
            source_instrument=self.source_instrument.name,
            source_port=self.source_port.name,
            target_instrument=self.target_instrument.name,
            target_port=self.target_port.name,
        )

    @classmethod
    def from_snapshot(cls, snapshot: AudioConnectionSnapshot, library: DeviceLibrary) -> AudioConnection:
        src_inst = library.get_instrument(snapshot.source_instrument)
        if src_inst is None:
            raise ValueError(
                f"Source instrument '{snapshot.source_instrument}' not found in library '{library.name}'"
            )
        tgt_inst = library.get_instrument(snapshot.target_instrument)
        if tgt_inst is None:
            raise ValueError(
                f"Target instrument '{snapshot.target_instrument}' not found in library '{library.name}'"
            )
        src_port = src_inst.get_output(snapshot.source_port)
        tgt_port = tgt_inst.get_input(snapshot.target_port)
        return cls(
            source_instrument=src_inst,
            source_port=src_port,
            target_instrument=tgt_inst,
            target_port=tgt_port,
        )
