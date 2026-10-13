import os
import unittest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from frangilive.app import FrangiliveApp
from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem
from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository
from frangilive.midi.infrastructure.mido_midi_gateway import MidoMidiGateway
from frangilive.ui.cues.cue_widget import CueWidget
from frangilive.ui.patcher.patcher_widget import PatcherWidget

os.environ["QT_QPA_PLATFORM"] = "offscreen"


class TestCueUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app_qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.mock_audio = MockAudioSystem()
        self.app = FrangiliveApp(
            device_repo=JsonDeviceRepository(),
            audio_router=self.mock_audio,
            audio_engine=self.mock_audio,
            midi_gateway=MidoMidiGateway(),
        )
        self.patcher_widget = PatcherWidget(app=self.app)
        self.cue_widget = CueWidget(app=self.app, patcher_widget=self.patcher_widget)
        self.cue_widget.resize(250, 600)

    def test_initial_state(self):
        self.assertEqual(len(self.app.cue_list), 0)
        self.assertEqual(self.cue_widget._cue_list_widget.count(), 0)
        self.assertIsNotNone(self.cue_widget._btn_delete)

    def test_create_new_cue_and_refresh(self):
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        self.app.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)

        # Click New Cue
        self.cue_widget._btn_new.click()

        self.assertEqual(len(self.app.cue_list), 1)
        self.assertEqual(self.cue_widget._cue_list_widget.count(), 1)
        self.assertEqual(self.cue_widget._cue_list_widget.currentRow(), 0)
        self.assertIn("Cue 1", self.cue_widget._cue_list_widget.item(0).text())
        self.assertIn("1 cables", self.cue_widget._cue_list_widget.item(0).text())

    def test_navigation_buttons(self):
        # Create Cue 1 (1 connection)
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        self.app.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)
        self.cue_widget.create_new_cue()

        # Create Cue 2 (empty patch)
        self.cue_widget.empty_patch()
        self.cue_widget.create_new_cue()

        self.assertEqual(len(self.app.cue_list), 2)
        self.assertEqual(self.app.cue_list.current_index, 1)
        self.assertEqual(len(self.app.patcher.connections), 0)

        # Go to first cue
        self.cue_widget._btn_first.click()
        self.assertEqual(self.app.cue_list.current_index, 0)
        self.assertEqual(len(self.app.patcher.connections), 1)
        self.assertEqual(self.cue_widget._cue_list_widget.currentRow(), 0)

        # Go to next cue
        self.cue_widget._btn_next.click()
        self.assertEqual(self.app.cue_list.current_index, 1)
        self.assertEqual(len(self.app.patcher.connections), 0)
        self.assertEqual(self.cue_widget._cue_list_widget.currentRow(), 1)

        # Go to previous cue
        self.cue_widget._btn_prev.click()
        self.assertEqual(self.app.cue_list.current_index, 0)
        self.assertEqual(len(self.app.patcher.connections), 1)
        self.assertEqual(self.cue_widget._cue_list_widget.currentRow(), 0)

    def test_save_current_cue_updates_patch(self):
        # Create Cue 1 (empty)
        self.cue_widget.create_new_cue()
        self.assertEqual(self.app.cue_list.current_cue.connection_count(), 0)

        # Add connection
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        self.app.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)

        # Save to current cue
        self.cue_widget.save_current_cue()
        self.assertEqual(self.app.cue_list.current_cue.connection_count(), 1)
        self.assertIn("1 cables", self.cue_widget._cue_list_widget.item(0).text())

    def test_delete_current_cue(self):
        # Create Cue 1 (1 connection)
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        self.app.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)
        self.cue_widget.create_new_cue()

        # Create Cue 2 (empty patch)
        self.cue_widget.empty_patch()
        self.cue_widget.create_new_cue()

        self.assertEqual(len(self.app.cue_list), 2)
        self.assertEqual(self.app.cue_list.current_index, 1)

        # Delete Cue 2
        self.cue_widget.delete_current_cue()

        self.assertEqual(len(self.app.cue_list), 1)
        self.assertEqual(self.app.cue_list.current_index, 0)
        self.assertEqual(self.cue_widget._cue_list_widget.count(), 1)
        self.assertEqual(self.cue_widget._cue_list_widget.currentRow(), 0)
        self.assertEqual(len(self.app.patcher.connections), 1)

        # Delete Cue 1 (last remaining cue)
        self.cue_widget.delete_current_cue()

        self.assertEqual(len(self.app.cue_list), 0)
        self.assertIsNone(self.app.cue_list.current_index)
        self.assertEqual(self.cue_widget._cue_list_widget.count(), 0)
        self.assertEqual(len(self.app.patcher.connections), 0)

    def test_empty_patch_clears_connections(self):
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        self.app.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)
        self.assertEqual(len(self.app.patcher.connections), 1)

        self.cue_widget.empty_patch()
        self.assertEqual(len(self.app.patcher.connections), 0)

    def test_list_widget_row_selection(self):
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        self.app.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)
        self.cue_widget.create_new_cue()

        self.cue_widget.empty_patch()
        self.cue_widget.create_new_cue()

        # Select row 0 in list
        self.cue_widget._cue_list_widget.setCurrentRow(0)
        self.assertEqual(self.app.cue_list.current_index, 0)
        self.assertEqual(len(self.app.patcher.connections), 1)


    def test_delete_button_hold_and_release_only_deletes_one_cue(self):
        # Create 3 cues
        self.cue_widget.create_new_cue() # Cue 1
        self.cue_widget.create_new_cue() # Cue 2
        self.cue_widget.create_new_cue() # Cue 3
        self.assertEqual(len(self.app.cue_list), 3)
        self.assertEqual(self.app.cue_list.current_index, 2)

        # Reconfigure button duration for fast test execution
        self.cue_widget._btn_delete.animation.setDuration(50)

        # Hold delete button until confirmed
        QTest.mousePress(self.cue_widget._btn_delete, Qt.MouseButton.LeftButton)
        QTest.qWait(100)
        # Release delete button
        QTest.mouseRelease(self.cue_widget._btn_delete, Qt.MouseButton.LeftButton)
        QTest.qWait(50)

        # Exactly ONE cue should be deleted, leaving 2 cues (Cue 1 and Cue 2)
        self.assertEqual(len(self.app.cue_list), 2)
        self.assertEqual(self.app.cue_list.current_index, 1)


if __name__ == "__main__":
    unittest.main()
