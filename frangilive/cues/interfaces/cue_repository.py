from abc import ABC, abstractmethod
from frangilive.devices.domain.device_library import DeviceLibrary
from frangilive.cues.domain.cue_list import CueList


class CueRepository(ABC):
    @abstractmethod
    def load_cues(self, library: DeviceLibrary) -> CueList | None:
        """Loads and returns the CueList if present in storage, or None."""
        pass

    @abstractmethod
    def save_cues(self, cue_list: CueList) -> None:
        """Saves the CueList to persistent storage."""
        pass
