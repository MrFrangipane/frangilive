from frangilive.patcher.domain.patcher import Patcher
from frangilive.cues.domain.cue import Cue
from frangilive.cues.domain.cue_list import CueList
from frangilive.devices.interfaces.device_repository import DeviceRepository
from frangilive.audio.interfaces.audio_router import AudioRouterGateway
from frangilive.audio.interfaces.audio_engine import AudioEngineGateway
from frangilive.midi.interfaces.midi import MidiGateway

from frangilive.patcher.application.manage_connections import ManageConnectionsUseCase
from frangilive.cues.application.manage_cues import ManageCuesUseCase
from frangilive.audio.application.manage_audio_engine import ManageAudioEngineUseCase
from frangilive.midi.application.forward_midi import ForwardMidiUseCase


class FrangiliveApp:
    def __init__(
            self,
            device_repo: DeviceRepository,
            audio_router: AudioRouterGateway,
            audio_engine: AudioEngineGateway,
            midi_gateway: MidiGateway
    ):
        self.device_repo = device_repo
        self.device_library = self.device_repo.load_library()
        self.patcher = Patcher(device_library=self.device_library)
        self.cue_list = CueList()

        self.manage_connections = ManageConnectionsUseCase(audio_router, self.patcher)
        self.manage_cues = ManageCuesUseCase(self.cue_list, self.manage_connections, self.patcher)
        self.manage_engine = ManageAudioEngineUseCase(audio_engine)
        self.forward_midi = ForwardMidiUseCase(midi_gateway)

    def connect(self, source_name: str, source_port_name: str, target_name: str, target_port_name: str) -> bool:
        return self.manage_connections.connect(source_name, source_port_name, target_name, target_port_name)

    def disconnect(self, source_name: str, source_port_name: str, target_name: str, target_port_name: str) -> bool:
        return self.manage_connections.disconnect(source_name, source_port_name, target_name, target_port_name)

    def empty_patch(self) -> None:
        self.manage_cues.empty_patch()

    def create_cue_from_current_patch(self, name: str | None = None) -> Cue:
        return self.manage_cues.create_cue_from_current_patch(name=name)

    def save_current_patch_to_current_cue(self) -> Cue | None:
        return self.manage_cues.save_current_patch_to_current_cue()

    def delete_current_cue(self) -> Cue | None:
        return self.manage_cues.delete_current_cue()

    def delete_cue(self, index: int | None = None) -> Cue | None:
        return self.manage_cues.delete_cue(index)

    def go_to_first_cue(self) -> Cue | None:
        return self.manage_cues.go_to_first_cue()

    def go_to_next_cue(self) -> Cue | None:
        return self.manage_cues.go_to_next_cue()

    def go_to_previous_cue(self) -> Cue | None:
        return self.manage_cues.go_to_previous_cue()

    def go_to_cue(self, index: int) -> Cue | None:
        return self.manage_cues.go_to_cue(index)
