import logging
import sys

from PySide6.QtWidgets import QApplication
from pyside6helpers.main_window import MainWindow
from pyside6helpers import css

from frangilive.infrastructure.persistence.json_device_repository import JsonDeviceRepository
from frangilive.infrastructure.midi.mido_midi_gateway import MidoMidiGateway
from frangilive.application.app import FrangiliveApp

if sys.platform == "linux":
    from frangilive.infrastructure.audio.jack_audio_router import JackAudioRouter
    audio_impl = JackAudioRouter()
else:
    from frangilive.infrastructure.audio.mock_audio_router import MockAudioRouter
    audio_impl = MockAudioRouter()

from frangilive.ui.patcher.patcher import PatcherWidget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    #
    # App
    frangilive_app = FrangiliveApp(
        device_repo=JsonDeviceRepository(),
        audio_router=audio_impl,
        audio_engine=audio_impl,
        midi_gateway=MidoMidiGateway()
    )

    # Start audio engine
    frangilive_app.manage_engine.start_engine(
        buffer_size=128,
        connection_type="USB",
        driver="alsa",
        interface_name="Fireface"
    )

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
