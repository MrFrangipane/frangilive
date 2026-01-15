import sys
from PySide6.QtWidgets import QApplication

from pyside6helpers.main_window import MainWindow
from pyside6helpers import css

if sys.platform == "linux":
    from frangilive.audio.router.raspberry_pi import RaspberryPiAudioRouter
    AudioRouter = RaspberryPiAudioRouter
else:
    from frangilive.audio.router.mock import MockAudioRouter
    AudioRouter = MockAudioRouter

from frangilive.ui.patcher.patcher import PatcherWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Frangilive")
    app.setOrganizationName("Frangitron")
    css.load_onto(app)

    window = MainWindow()
    window.setCentralWidget(PatcherWidget())
    window.show()

    sys.exit(app.exec())
