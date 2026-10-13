import json
import os
import tempfile
import unittest
from pathlib import Path

from frangilive.app import FrangiliveApp
from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem
from frangilive.cues.domain.cue import Cue
from frangilive.cues.domain.cue_list import CueList
from frangilive.cues.infrastructure.json_cue_repository import JsonCueRepository
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.domain.audio_port import AudioPort
from frangilive.devices.domain.device_library import DeviceLibrary
from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository
from frangilive.midi.infrastructure.mido_midi_gateway import MidoMidiGateway
from frangilive.patcher.domain.audio_connection import AudioConnection


class TestCuePersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.cues_json_path = self.temp_path / "cues.json"

        self.inst_a = AudioInstrument(
            name="SynthA",
            inputs=[AudioPort("In1", left=1)],
            outputs=[AudioPort("Out1", left=1)],
        )
        self.inst_b = AudioInstrument(
            name="EffectB",
            inputs=[AudioPort("In1", left=2)],
            outputs=[AudioPort("Out1", left=2)],
        )
        self.library = DeviceLibrary(name="TestLib", audio_instruments=[self.inst_a, self.inst_b])

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_non_existent_file_returns_none(self):
        repo = JsonCueRepository(file_path=self.temp_path / "does_not_exist.json")
        loaded = repo.load_cues(self.library)
        self.assertIsNone(loaded)

    def test_save_and_load_roundtrip(self):
        repo = JsonCueRepository(file_path=self.cues_json_path)

        conn = AudioConnection(
            source_instrument=self.inst_a,
            source_port=self.inst_a.outputs[0],
            target_instrument=self.inst_b,
            target_port=self.inst_b.inputs[0],
        )
        cue1 = Cue(name="Intro", connections=[conn])
        cue2 = Cue(name="Chorus", connections=[])
        cue_list = CueList(cues=[cue1, cue2], current_index=0)

        repo.save_cues(cue_list)
        self.assertTrue(self.cues_json_path.exists())

        # Verify JSON content is formatted nicely
        with open(self.cues_json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        self.assertEqual(len(raw_data["cues"]), 2)
        self.assertEqual(raw_data["current_index"], 0)
        self.assertEqual(raw_data["cues"][0]["name"], "Intro")

        # Load back
        loaded_cue_list = repo.load_cues(self.library)
        self.assertIsNotNone(loaded_cue_list)
        self.assertEqual(len(loaded_cue_list), 2)
        self.assertEqual(loaded_cue_list.current_index, 0)
        self.assertEqual(loaded_cue_list[0].name, "Intro")
        self.assertEqual(len(loaded_cue_list[0].connections), 1)
        self.assertEqual(loaded_cue_list[0].connections[0], conn)
        self.assertEqual(loaded_cue_list[1].name, "Chorus")
        self.assertEqual(len(loaded_cue_list[1].connections), 0)

    def test_load_corrupted_json_returns_none(self):
        corrupt_file = self.temp_path / "corrupt.json"
        with open(corrupt_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        repo = JsonCueRepository(file_path=corrupt_file)
        self.assertIsNone(repo.load_cues(self.library))

    def test_save_creates_nested_directories_if_needed(self):
        nested_file = self.temp_path / "nested" / "sub" / "cues.json"
        repo = JsonCueRepository(file_path=nested_file)
        cue_list = CueList(cues=[Cue(name="Solo")], current_index=0)

        repo.save_cues(cue_list)
        self.assertTrue(nested_file.exists())
        loaded = repo.load_cues(self.library)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 1)

    def test_app_loads_cues_on_startup_and_applies_current_cue_patch(self):
        # 1. Pre-save a cue list with an active patch
        repo = JsonCueRepository(file_path=self.cues_json_path)

        device_repo = JsonDeviceRepository()
        real_library = device_repo.load_library()
        digitakt = real_library.get_instrument("Digitakt")
        main_lr = real_library.get_instrument("Main LR")

        conn = AudioConnection(
            source_instrument=digitakt,
            source_port=digitakt.get_default_output(),
            target_instrument=main_lr,
            target_port=main_lr.get_default_input(),
        )
        pre_saved_cues = CueList(
            cues=[Cue(name="Song 1", connections=[conn])],
            current_index=0,
        )
        repo.save_cues(pre_saved_cues)

        # 2. Start app with this repo
        mock_audio = MockAudioSystem()
        app = FrangiliveApp(
            device_repo=device_repo,
            audio_router=mock_audio,
            audio_engine=mock_audio,
            midi_gateway=MidoMidiGateway(),
            cue_repo=repo,
            auto_save_cues_on_exit=False,
        )

        self.assertEqual(len(app.cue_list), 1)
        self.assertEqual(app.cue_list.current_index, 0)
        self.assertEqual(app.cue_list.current_cue.name, "Song 1")
        # Patcher connections should be applied from the active cue
        self.assertEqual(len(app.patcher.connections), 1)
        self.assertEqual(list(app.patcher.connections)[0], conn)

    def test_app_save_and_reopen(self):
        repo = JsonCueRepository(file_path=self.cues_json_path)
        mock_audio = MockAudioSystem()
        device_repo = JsonDeviceRepository()

        # Instance 1: Create cue and save
        app1 = FrangiliveApp(
            device_repo=device_repo,
            audio_router=mock_audio,
            audio_engine=mock_audio,
            midi_gateway=MidoMidiGateway(),
            cue_repo=repo,
            auto_save_cues_on_exit=False,
        )
        digitakt = app1.device_library.get_instrument("Digitakt")
        main_lr = app1.device_library.get_instrument("Main LR")
        app1.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)
        app1.create_cue_from_current_patch(name="Live Track 1")
        app1.save_cues()

        # Instance 2: Loads persisted cues
        app2 = FrangiliveApp(
            device_repo=device_repo,
            audio_router=mock_audio,
            audio_engine=mock_audio,
            midi_gateway=MidoMidiGateway(),
            cue_repo=repo,
            auto_save_cues_on_exit=False,
        )
        self.assertEqual(len(app2.cue_list), 1)
        self.assertEqual(app2.cue_list[0].name, "Live Track 1")
        self.assertEqual(len(app2.patcher.connections), 1)


if __name__ == "__main__":
    unittest.main()
