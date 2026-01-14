from frangilive.audio.interface_connection_type import InterfaceConnectionType
from frangilive.audio.jack_options import JackOptions
from frangilive.audio.router.abstract import AbstractAudioRouter
from frangilive.audio.typing import AudioDriver


def make_audio_router(class_, interface_name: str, buffer_size: int, connection_type: InterfaceConnectionType, driver: AudioDriver) -> AbstractAudioRouter:
    audio_router = class_()
    if not audio_router.find_audio_interface(name=interface_name):
        raise RuntimeError("No audio interface found")

    audio_router.start_jack_server(JackOptions(
        interface_connection_type=connection_type,
        buffer_size=buffer_size,
        driver=driver
    ))
    audio_router.start_overwitch()
    audio_router.activate_jack_client()
    audio_router.remove_all_audio_connections()

    return audio_router
