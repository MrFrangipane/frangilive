from frangilive.audio.abstract import AbstractAudioMidi
from frangilive.audio.audio_interface import AudioInterface


class MockAudioMidi(AbstractAudioMidi):

    def find_audio_interface(self, name: str) -> AudioInterface | None:
        return True
