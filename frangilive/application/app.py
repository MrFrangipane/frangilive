from frangilive.domain.models.patcher import Patcher
from frangilive.interfaces.repositories.device_repository import DeviceRepository
from frangilive.interfaces.gateways.audio_router import AudioRouterGateway
from frangilive.interfaces.gateways.audio_engine import AudioEngineGateway
from frangilive.interfaces.gateways.midi import MidiGateway

from frangilive.application.use_cases.manage_connections import ManageConnectionsUseCase
from frangilive.application.use_cases.manage_audio_engine import ManageAudioEngineUseCase
from frangilive.application.use_cases.forward_midi import ForwardMidiUseCase


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

        self.manage_connections = ManageConnectionsUseCase(audio_router, self.patcher)
        self.manage_engine = ManageAudioEngineUseCase(audio_engine)
        self.forward_midi = ForwardMidiUseCase(midi_gateway)

    def connect(self, source_name: str, source_port_name: str, target_name: str, target_port_name: str) -> bool:
        return self.manage_connections.connect(source_name, source_port_name, target_name, target_port_name)

    def disconnect(self, source_name: str, source_port_name: str, target_name: str, target_port_name: str) -> bool:
        return self.manage_connections.disconnect(source_name, source_port_name, target_name, target_port_name)
