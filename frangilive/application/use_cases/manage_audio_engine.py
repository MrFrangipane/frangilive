from frangilive.interfaces.gateways.audio_engine import AudioEngineGateway


class ManageAudioEngineUseCase:
    def __init__(self, engine_gateway: AudioEngineGateway):
        self.engine_gateway = engine_gateway

    def start_engine(self, **kwargs) -> None:
        self.engine_gateway.start(**kwargs)

    def stop_engine(self) -> None:
        self.engine_gateway.stop()

    def is_engine_running(self) -> bool:
        return self.engine_gateway.is_running()
