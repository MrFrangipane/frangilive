from dataclasses import dataclass, field
from typing import Iterator
from frangilive.patcher.domain.audio_connection import AudioConnection
from frangilive.cues.domain.cue import Cue


@dataclass
class CueList:
    """
    Manages an ordered list of Cues and tracks the current active cue index.
    """
    cues: list[Cue] = field(default_factory=list)
    current_index: int | None = None

    def __post_init__(self):
        self.cues = list(self.cues)
        if not self.cues:
            self.current_index = None
        elif self.current_index is None:
            self.current_index = 0
        else:
            self.current_index = max(0, min(self.current_index, len(self.cues) - 1))


    @property
    def current_cue(self) -> Cue | None:
        if self.current_index is not None and 0 <= self.current_index < len(self.cues):
            return self.cues[self.current_index]
        return None

    def add_cue(self, cue: Cue) -> Cue:
        self.cues.append(cue)
        self.current_index = len(self.cues) - 1
        return cue

    def create_cue_from_connections(
        self, connections: list[AudioConnection], name: str | None = None
    ) -> Cue:
        cue_name = name if name is not None else f"Cue {len(self.cues) + 1}"
        cue = Cue(name=cue_name, connections=connections)
        return self.add_cue(cue)

    def save_current_cue(self, connections: list[AudioConnection]) -> Cue | None:
        cue = self.current_cue
        if cue is not None:
            cue.set_connections(connections)
            return cue
        return None

    def go_to_first_cue(self) -> Cue | None:
        if not self.cues:
            return None
        self.current_index = 0
        return self.cues[0]

    def go_to_next_cue(self) -> Cue | None:
        if not self.cues:
            return None
        if self.current_index is None:
            self.current_index = 0
        elif self.current_index < len(self.cues) - 1:
            self.current_index += 1
        return self.cues[self.current_index]

    def go_to_previous_cue(self) -> Cue | None:
        if not self.cues:
            return None
        if self.current_index is None:
            self.current_index = 0
        elif self.current_index > 0:
            self.current_index -= 1
        return self.cues[self.current_index]

    def go_to_cue(self, index: int) -> Cue | None:
        if 0 <= index < len(self.cues):
            self.current_index = index
            return self.cues[index]
        return None

    def remove_cue(self, index: int) -> Cue | None:
        if not (0 <= index < len(self.cues)):
            return None
        removed = self.cues.pop(index)
        if not self.cues:
            self.current_index = None
        elif self.current_index is not None:
            if self.current_index >= len(self.cues):
                self.current_index = len(self.cues) - 1
            elif self.current_index > index:
                self.current_index -= 1
        return removed

    def delete_current_cue(self) -> Cue | None:
        if self.current_index is None:
            return None
        return self.remove_cue(self.current_index)

    def clear(self) -> None:
        self.cues.clear()
        self.current_index = None

    def __len__(self) -> int:
        return len(self.cues)

    def __getitem__(self, index: int) -> Cue:
        return self.cues[index]

    def __iter__(self) -> Iterator[Cue]:
        return iter(self.cues)
