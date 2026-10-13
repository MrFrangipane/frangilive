import json
import logging
from pathlib import Path

from frangilive.devices.domain.device_library import DeviceLibrary
from frangilive.cues.domain.cue_list import CueList, CueListSnapshot
from frangilive.cues.interfaces.cue_repository import CueRepository

logger = logging.getLogger(__name__)


class JsonCueRepository(CueRepository):
    def __init__(self, file_path: str | Path = "cues.json"):
        self.file_path = Path(file_path)

    def load_cues(self, library: DeviceLibrary) -> CueList | None:
        if not self.file_path.exists():
            return None
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            snapshot = CueListSnapshot.from_dict(data)
            return snapshot.to_cue_list(library)
        except Exception as e:
            logger.error("Failed to load cues from %s: %s", self.file_path, e)
            return None

    def save_cues(self, cue_list: CueList) -> None:
        try:
            if self.file_path.parent and str(self.file_path.parent) != "." and not self.file_path.parent.exists():
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot = cue_list.to_snapshot()
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, indent=2)
        except Exception as e:
            logger.error("Failed to save cues to %s: %s", self.file_path, e)
