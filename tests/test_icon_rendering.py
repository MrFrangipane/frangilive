import os
import tempfile
import unittest
from importlib.resources import files, as_file

from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from frangilive.app import FrangiliveApp
from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem
from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository
from frangilive.midi.infrastructure.mido_midi_gateway import MidoMidiGateway
from frangilive.patcher.domain.patcher import Patcher
from frangilive.ui.patcher.patcher_widget import PatcherWidget
from scripts.generate_icons import (
    generate_icon,
    generate_syntakt_icon,
    generate_digitakt_icon,
    generate_digitone_icon,
    generate_microphone_icon,
    generate_main_lr_icon,
    generate_mf101_icon,
    generate_murf_icon,
    generate_time_factor_icon,
    generate_big_sky_icon,
)


class TestIconRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app_instance = QApplication([])
        else:
            cls.app_instance = QApplication.instance()

    def setUp(self):
        self.device_repo = JsonDeviceRepository()
        self.device_lib = self.device_repo.load_library()
        self.mock_audio = MockAudioSystem()
        self.app = FrangiliveApp(
            device_repo=self.device_repo,
            audio_router=self.mock_audio,
            audio_engine=self.mock_audio,
            midi_gateway=MidoMidiGateway(),
            auto_save_cues_on_exit=False,
        )

    def test_device_library_icon_extensions_are_svg(self):
        for instrument in self.device_lib.audio_instruments:
            self.assertIsNotNone(instrument.icon_name)
            self.assertTrue(
                instrument.icon_name.endswith(".svg"),
                f"Instrument {instrument.name} icon {instrument.icon_name} does not end with .svg",
            )

    def test_all_svg_icons_exist_and_are_valid(self):
        icons_resource = files("frangilive.resources.icons")
        for instrument in self.device_lib.audio_instruments:
            icon_path = icons_resource.joinpath(instrument.icon_name)
            with as_file(icon_path) as p:
                self.assertTrue(os.path.exists(p), f"Icon file {p} does not exist")
                renderer = QSvgRenderer(str(p))
                self.assertTrue(renderer.isValid(), f"Icon {instrument.icon_name} is not a valid SVG")

    def test_patcher_widget_loads_svg_icons(self):
        widget = PatcherWidget(app=self.app)
        for instrument in self.device_lib.audio_instruments:
            self.assertIn(instrument.name, widget._icons)
            icon = widget._icons[instrument.name]
            self.assertIsInstance(icon, QSvgRenderer)
            self.assertTrue(icon.isValid())

    def test_patcher_widget_renders_with_svg_icons(self):
        widget = PatcherWidget(app=self.app)
        widget.resize(800, 600)
        image = QImage(800, 600, QImage.Format_ARGB32)
        widget.render(image)
        self.assertFalse(image.isNull())

    def test_icon_generators_produce_valid_svg_files(self):
        generators = [
            generate_syntakt_icon,
            generate_digitakt_icon,
            generate_digitone_icon,
            generate_microphone_icon,
            generate_main_lr_icon,
            generate_mf101_icon,
            generate_murf_icon,
            generate_time_factor_icon,
            generate_big_sky_icon,
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            for idx, gen in enumerate(generators):
                path = os.path.join(tmpdir, f"test_icon_{idx}.svg")
                gen(path)
                self.assertTrue(os.path.exists(path))
                renderer = QSvgRenderer(path)
                self.assertTrue(renderer.isValid(), f"Generator {gen.__name__} failed to produce valid SVG")


if __name__ == "__main__":
    unittest.main()
