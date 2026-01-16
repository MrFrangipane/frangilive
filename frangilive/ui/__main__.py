import logging
import sys

from PySide6.QtWidgets import QApplication
from pyside6helpers.main_window import MainWindow
from pyside6helpers import css

from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository
from frangilive.midi.infrastructure.mido_midi_gateway import MidoMidiGateway
from frangilive.app import FrangiliveApp

if sys.platform == "linux":
    from frangilive.audio.infrastructure.jack_audio_system import JackAudioSystem
    audio_system = JackAudioSystem()
else:
    from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem
    audio_system = MockAudioSystem()

from frangilive.ui.patcher.patcher import PatcherWidget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    #
    # App
    frangilive_app = FrangiliveApp(
        device_repo=JsonDeviceRepository(),
        audio_router=audio_system,
        audio_engine=audio_system,
        midi_gateway=MidoMidiGateway()
    )

    # Start the audio engine
    frangilive_app.manage_engine.start_engine(
        buffer_size=128,
        connection_type="USB",
        driver="alsa",
        interface_name="Fireface"
    )
    frangilive_app.manage_connections.clear_all_connections()

    #
    # Ui
    app = QApplication(sys.argv)
    app.setApplicationName("Frangilive")
    app.setOrganizationName("Frangitron")
    css.load_onto(app)

    patcher_widget = PatcherWidget(app=frangilive_app)

    window = MainWindow()
    window.setCentralWidget(patcher_widget)
    window.show()

    sys.exit(app.exec())
