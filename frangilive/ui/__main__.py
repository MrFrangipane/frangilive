import logging
import sys

from PySide6.QtWidgets import QApplication

from pyside6helpers.main_window import MainWindow
from pyside6helpers import css

from frangilive.audio.driver import AudioDriver
from frangilive.audio.interface_connection_type import InterfaceConnectionType
from frangilive.audio.router.router_factory import make_audio_router

if sys.platform == "linux":
    from frangilive.audio.router.raspberry_pi import RaspberryPiAudioRouter
    AudioRouter = RaspberryPiAudioRouter
else:
    from frangilive.audio.router.mock import MockAudioRouter
    AudioRouter = MockAudioRouter

from frangilive.ui.patcher.patcher import PatcherWidget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    #
    # Actual Audio
    audio_router = make_audio_router(
        buffer_size=128,
        class_=AudioRouter,
        connection_type=InterfaceConnectionType.USB,
        driver=AudioDriver.Alsa,
        interface_name="Fireface"
    )

    #
    # Ui
    app = QApplication(sys.argv)
    app.setApplicationName("Frangilive")
    app.setOrganizationName("Frangitron")
    css.load_onto(app)

    patcher_widget = PatcherWidget()
    patcher_widget.connected.connect(audio_router.connect)
    patcher_widget.disconnected.connect(audio_router.disconnect)

    window = MainWindow()
    window.setCentralWidget(patcher_widget)
    window.show()

    sys.exit(app.exec())
