from frangilive.audiomidi.abstract import AbstractAudioMidi
from frangilive.audiomidi.audio_interface import AudioInterface


class MockAudioMidi(AbstractAudioMidi):

    def find_audio_interface(self, name: str) -> AudioInterface | None:
        return True
