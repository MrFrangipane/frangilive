from dataclasses import dataclass


@dataclass(frozen=True)
class AudioPort:
    name: str
    left: str
    right: str | None = None

    @property
    def is_stereo(self) -> bool:
        return self.right is not None
