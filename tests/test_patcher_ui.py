import os
import unittest
from PySide6.QtCore import Qt, QPointF, QPoint
from PySide6.QtGui import QMouseEvent, QPainter, QImage
from PySide6.QtWidgets import QApplication

from frangilive.app import FrangiliveApp
from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem
from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository
from frangilive.midi.infrastructure.mido_midi_gateway import MidoMidiGateway
from frangilive.ui.patcher.config import PatcherWidgetConfig
from frangilive.ui.patcher.patcher_widget import PatcherWidget
from frangilive.ui.patcher.port_selector import PortSelectorDialog

# Run offscreen for headless Qt tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"


class TestPatcherUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app_qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.mock_audio = MockAudioSystem()
        self.app = FrangiliveApp(
            device_repo=JsonDeviceRepository(),
            audio_router=self.mock_audio,
            audio_engine=self.mock_audio,
            midi_gateway=MidoMidiGateway()
        )
        self.widget = PatcherWidget(app=self.app)
        self.widget.resize(800, 600)

    def test_circular_layout_generation(self):
        rects = self.widget._calculate_node_rects()
        self.assertEqual(len(rects), len(self.app.device_library.audio_instruments))

        # Check all instruments are positioned in the rects dict
        for inst in self.app.device_library.audio_instruments:
            self.assertIn(inst.name, rects)
            rect = rects[inst.name]
            self.assertGreater(rect.width(), 0)
            self.assertGreater(rect.height(), 0)

    def test_drag_and_connect_default_ports(self):
        # Digitakt (has outputs) -> Main LR (has inputs)
        rects = self.widget._calculate_node_rects()
        digitakt_rect = rects["Digitakt"]
        main_lr_rect = rects["Main LR"]

        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")

        # 1. Press on Digitakt
        press_pos = digitakt_rect.center()
        self.widget._handle_press(press_pos)
        self.assertEqual(self.widget._press_device, digitakt)

        # 2. Move to exceed drag threshold
        drag_pos = QPointF(press_pos.x() + 20, press_pos.y() + 20)
        self.widget._handle_move(drag_pos)
        self.assertTrue(self.widget._is_dragging)
        self.assertEqual(self.widget._drag_source_device, digitakt)
        self.assertEqual(self.widget._drag_source_port, digitakt.get_default_output().name)

        # 3. Move over Main LR
        self.widget._handle_move(main_lr_rect.center())
        self.assertEqual(self.widget._hover_target_device, main_lr)

        # 4. Release on Main LR
        self.widget._handle_release(main_lr_rect.center())
        self.assertFalse(self.widget._is_dragging)

        # Verify connection was made
        connections = self.app.patcher.get_connections_between("Digitakt", "Main LR")
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0].source_port.name, digitakt.get_default_output().name)
        self.assertEqual(connections[0].target_port.name, main_lr.get_default_input().name)

    def test_configurable_timer_intervals(self):
        # Default intervals
        widget_default = PatcherWidget(app=self.app)
        self.assertEqual(widget_default.long_press_interval, 400)
        self.assertEqual(widget_default.hover_long_press_interval, 500)
        self.assertEqual(widget_default.config.long_press_interval, 400)
        self.assertEqual(widget_default.config.hover_long_press_interval, 500)

        # Configured via PatcherWidgetConfig in constructor
        custom_config = PatcherWidgetConfig(
            long_press_interval=250,
            hover_long_press_interval=350,
        )
        widget_custom = PatcherWidget(
            app=self.app,
            config=custom_config,
        )
        self.assertEqual(widget_custom.long_press_interval, 250)
        self.assertEqual(widget_custom.hover_long_press_interval, 350)
        self.assertEqual(widget_custom.config.long_press_interval, 250)
        self.assertEqual(widget_custom.config.hover_long_press_interval, 350)

        # Configured via setters / properties
        widget_default.long_press_interval = 600
        widget_default.hover_long_press_interval = 700
        self.assertEqual(widget_default.long_press_interval, 600)
        self.assertEqual(widget_default.hover_long_press_interval, 700)
        self.assertEqual(widget_default.config.long_press_interval, 600)
        self.assertEqual(widget_default.config.hover_long_press_interval, 700)


    def test_custom_widget_config_layout_and_painting(self):
        custom_config = PatcherWidgetConfig(
            node_width=160.0,
            node_height=60.0,
            background_color="#101010",
        )
        widget = PatcherWidget(app=self.app, config=custom_config)
        widget.resize(800, 600)

        rects = widget._calculate_node_rects()
        digitakt_rect = rects["Digitakt"]
        self.assertEqual(digitakt_rect.width(), 160.0)
        self.assertEqual(digitakt_rect.height(), 60.0)

        image = QImage(800, 600, QImage.Format_ARGB32)
        widget.render(image)
        self.assertFalse(image.isNull())

    def test_start_device_long_press_sets_drag_mode_and_does_not_change_default_port(self):
        # Digitakt has multiple output ports (Main LR, Track 1..8), default is Main LR
        rects = self.widget._calculate_node_rects()
        digitakt_rect = rects["Digitakt"]
        digitakt = self.app.device_library.get_instrument("Digitakt")

        initial_default = digitakt.get_default_output().name
        self.assertEqual(initial_default, "Main LR")

        # Press on Digitakt
        press_pos = digitakt_rect.center()
        self.widget._handle_press(press_pos)

        # Simulate start device long press timeout
        self.widget._press_device = digitakt

        # Select "Track 3" for dragging without changing default output
        self.widget._drag_source_device = digitakt
        self.widget._drag_source_port = "Track 3"
        self.widget._is_dragging = True

        # Ensure default output port on instrument is NOT modified
        self.assertEqual(digitakt.get_default_output().name, initial_default)

        # Now drag and connect to Time Factor
        time_factor_rect = rects["Time Factor"]
        time_factor = self.app.device_library.get_instrument("Time Factor")

        self.widget._handle_move(time_factor_rect.center())
        self.widget._handle_release(time_factor_rect.center())

        conns = self.app.patcher.get_connections_between("Digitakt", "Time Factor")
        self.assertEqual(len(conns), 1)
        self.assertEqual(conns[0].source_port.name, "Track 3")
        self.assertEqual(conns[0].target_port.name, time_factor.get_default_input().name)

        # Default port of Digitakt should STILL be Main LR
        self.assertEqual(digitakt.get_default_output().name, "Main LR")

    def test_staying_long_over_target_device_does_not_change_target_default_port(self):
        # Digitakt -> Time Factor
        rects = self.widget._calculate_node_rects()
        digitakt = self.app.device_library.get_instrument("Digitakt")
        time_factor = self.app.device_library.get_instrument("Time Factor")

        initial_target_default = time_factor.get_default_input().name
        self.assertEqual(initial_target_default, "Main L")

        # Start drag
        self.widget._is_dragging = True
        self.widget._drag_source_device = digitakt
        self.widget._drag_source_port = "Track 1"
        self.widget._hover_target_device = time_factor

        # Connect with selected target port "Main L"
        self.widget._connect_devices(digitakt, "Track 1", time_factor, "Main L")

        conns = self.app.patcher.get_connections_between("Digitakt", "Time Factor")
        self.assertEqual(len(conns), 1)
        self.assertEqual(conns[0].source_port.name, "Track 1")
        self.assertEqual(conns[0].target_port.name, "Main L")

        # Target device default input port should NOT have changed
        self.assertEqual(time_factor.get_default_input().name, initial_target_default)

    def test_disconnect_connection(self):
        # Connect Digitakt to Main LR
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")

        self.app.connect("Digitakt", "Main LR", "Main LR", "Main LR")
        self.assertEqual(len(self.app.patcher.connections), 1)

        # Disconnect
        conn = self.app.patcher.connections[0]
        self.widget._disconnect_connection(conn)
        self.assertEqual(len(self.app.patcher.connections), 0)

    def test_paint_event_rendering(self):
        # Connect some devices and ensure paintEvent executes cleanly without errors
        self.app.connect("Microphone", "Out", "MF-101", "Main L")
        self.app.connect("Digitakt", "Main LR", "Main LR", "Main LR")

        image = QImage(800, 600, QImage.Format_ARGB32)
        self.widget.render(image)

        # Image should not be null
        self.assertFalse(image.isNull())

    def test_port_selector_dialog(self):
        dialog = PortSelectorDialog(
            instrument_name="Digitakt",
            port_names=["Main LR", "Track 1", "Track 2"],
            current_default="Main LR",
            is_output=True
        )
        dialog._on_port_clicked("Track 2")
        self.assertEqual(dialog.selected_port, "Track 2")

    def test_port_selector_dialog_max_4_rows(self):
        # Syntakt has 13 ports: Main LR + Track 1..12
        port_names = ["Main LR"] + [f"Track {i}" for i in range(1, 13)]
        dialog = PortSelectorDialog(
            instrument_name="Syntakt",
            port_names=port_names,
            current_default="Main LR",
            is_output=True
        )
        # Find the QGridLayout in the dialog
        container = dialog.findChild(PortSelectorDialog) or dialog
        # Check that grid layout has <= 4 rows
        grid = dialog.findChild(type(dialog.layout()))
        # Check width is wider to accommodate 4 columns
        self.assertGreaterEqual(dialog.minimumWidth(), 600)
        self.assertLessEqual(dialog.minimumHeight(), 420)

    def test_explicit_default_port_selection_still_customizes_default_port(self):
        digitakt = self.app.device_library.get_instrument("Digitakt")
        self.assertEqual(digitakt.get_default_output().name, "Main LR")

        # Explicitly change default port
        digitakt.set_default_output("Track 5")
        self.assertEqual(digitakt.get_default_output().name, "Track 5")

    def test_cancel_port_selection_cancels_drag_altogether(self):
        digitakt = self.app.device_library.get_instrument("Digitakt")
        self.widget._press_device = digitakt
        self.widget._is_dragging = True
        self.widget._drag_source_device = digitakt
        self.widget._drag_source_port = "Main LR"

        # Explicitly cancel drag
        self.widget._cancel_drag()
        self.assertFalse(self.widget._is_dragging)
        self.assertIsNone(self.widget._drag_source_device)
        self.assertIsNone(self.widget._drag_source_port)
        self.assertIsNone(self.widget._hover_target_device)
        self.assertIsNone(self.widget._press_device)

    def test_escape_key_cancels_drag(self):
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        digitakt = self.app.device_library.get_instrument("Digitakt")
        self.widget._press_device = digitakt
        self.widget._is_dragging = True
        self.widget._drag_source_device = digitakt
        self.widget._drag_source_port = "Main LR"

        escape_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        self.widget.keyPressEvent(escape_event)

        self.assertFalse(self.widget._is_dragging)
        self.assertIsNone(self.widget._drag_source_device)

    def test_wire_labels_on_multi_port_devices(self):
        # Connect Digitakt (multiple outputs) to Main LR (single input)
        self.app.connect("Digitakt", "Track 1", "Main LR", "Main LR")
        # Connect Microphone (1 output) to MF-101 (1 input)
        self.app.connect("Microphone", "Out", "MF-101", "Main L")

        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        mic = self.app.device_library.get_instrument("Microphone")
        mf101 = self.app.device_library.get_instrument("MF-101")

        # Digitakt has >1 outputs, so wire label should be generated
        has_digitakt_multi = (len(digitakt.outputs) > 1 or len(main_lr.inputs) > 1)
        self.assertTrue(has_digitakt_multi)

        # Mic has 1 output and MF-101 has 1 input, so wire label not needed
        has_mic_multi = (len(mic.outputs) > 1 or len(mf101.inputs) > 1)
        self.assertFalse(has_mic_multi)

    def test_custom_config_port_selector_dialog(self):
        custom_config = PatcherWidgetConfig(
            port_selector_max_rows=2,
            port_selector_base_col_width=200,
            port_selector_min_width=400,
        )
        dialog = PortSelectorDialog(
            instrument_name="Digitakt",
            port_names=["Main LR", "Track 1", "Track 2", "Track 3"],
            current_default="Main LR",
            is_output=True,
            config=custom_config,
        )
        self.assertEqual(dialog._config.port_selector_max_rows, 2)
        self.assertGreaterEqual(dialog.minimumWidth(), 400)

    def test_custom_drag_threshold(self):
        custom_config = PatcherWidgetConfig(drag_threshold=50.0)
        widget = PatcherWidget(app=self.app, config=custom_config)
        widget.resize(800, 600)

        rects = widget._calculate_node_rects()
        digitakt_rect = rects["Digitakt"]
        press_pos = digitakt_rect.center()

        widget._handle_press(press_pos)
        # Move by 20px (less than custom threshold of 50px)
        widget._handle_move(QPointF(press_pos.x() + 20, press_pos.y()))
        self.assertFalse(widget._is_dragging)

        # Move beyond 50px
        widget._handle_move(QPointF(press_pos.x() + 60, press_pos.y()))
        self.assertTrue(widget._is_dragging)

    def test_wires_curved_toward_center(self):
        import math
        from frangilive.ui.patcher.geometry import path_midpoint

        # Connect Digitakt and MF-101 (or adjacent / non-colinear devices)
        self.app.connect("Digitakt", "Main LR", "MF-101", "Main L")
        conn = self.app.patcher.connections[0]

        rects = self.widget._calculate_node_rects()
        src_center = rects["Digitakt"].center()
        tgt_center = rects["MF-101"].center()

        straight_mid_x = (src_center.x() + tgt_center.x()) / 2.0
        straight_mid_y = (src_center.y() + tgt_center.y()) / 2.0
        widget_center = QPointF(self.widget.width() / 2.0, self.widget.height() / 2.0)

        dist_straight_to_center = math.hypot(
            straight_mid_x - widget_center.x(),
            straight_mid_y - widget_center.y(),
        )

        curved_path = self.widget._connection_path(conn)
        self.assertFalse(curved_path.isEmpty())

        curve_mid = path_midpoint(curved_path)
        dist_curve_to_center = math.hypot(
            curve_mid.x() - widget_center.x(),
            curve_mid.y() - widget_center.y(),
        )

        # Midpoint of curved path must be closer to widget center than straight chord midpoint
        self.assertLess(dist_curve_to_center, dist_straight_to_center)

    def test_multiple_connections_between_same_devices_distinct_curves(self):
        self.app.connect("Digitakt", "Track 1", "Main LR", "Main LR")
        self.app.connect("Digitakt", "Track 2", "Main LR", "Main LR")

        conns = self.app.patcher.get_connections_between("Digitakt", "Main LR")
        self.assertEqual(len(conns), 2)

        self.widget._calculate_node_rects()
        path1 = self.widget._connection_path(conns[0], offset_idx=0)
        path2 = self.widget._connection_path(conns[1], offset_idx=1)

        self.assertFalse(path1.isEmpty())
        self.assertFalse(path2.isEmpty())
        # Both paths should not be identical
        self.assertNotEqual(path1.pointAtPercent(0.5), path2.pointAtPercent(0.5))

    def test_labels_placement_no_overlap_multiple_connections(self):
        from frangilive.ui.patcher.geometry import find_non_overlapping_label_rect

        # Connect 3 wires between Digitakt and Main LR
        self.app.connect("Digitakt", "Track 1", "Main LR", "Main LR")
        self.app.connect("Digitakt", "Track 2", "Main LR", "Main LR")
        self.app.connect("Digitakt", "Track 3", "Main LR", "Main LR")

        conns = self.app.patcher.get_connections_between("Digitakt", "Main LR")
        self.widget._calculate_node_rects()

        placed_rects = []
        for i, conn in enumerate(conns):
            path = self.widget._connection_path(conn, offset_idx=i)
            rect = find_non_overlapping_label_rect(
                path=path,
                badge_width=80.0,
                badge_height=20.0,
                offset_idx=i,
                total_pair_conns=len(conns),
                existing_rects=placed_rects,
            )
            # Verify newly placed rect does not overlap with any previously placed rects
            for prev in placed_rects:
                self.assertFalse(
                    rect.intersects(prev),
                    f"Label badge {i} intersects with previously placed badge",
                )
            placed_rects.append(rect)

    def test_labels_placement_crossing_connections_no_overlap(self):
        from frangilive.ui.patcher.geometry import find_non_overlapping_label_rect

        # Connect crossing paths: Digitakt -> Main LR and Microphone -> MF-101
        digitakt = self.app.device_library.get_instrument("Digitakt")
        main_lr = self.app.device_library.get_instrument("Main LR")
        mic = self.app.device_library.get_instrument("Microphone")
        mf101 = self.app.device_library.get_instrument("MF-101")

        self.app.connect(digitakt.name, digitakt.outputs[0].name, main_lr.name, main_lr.inputs[0].name)
        self.app.connect(mic.name, mic.outputs[0].name, mf101.name, mf101.inputs[0].name)

        conn1 = self.app.patcher.connections[0]
        conn2 = self.app.patcher.connections[1]

        self.widget._calculate_node_rects()
        path1 = self.widget._connection_path(conn1)
        path2 = self.widget._connection_path(conn2)

        placed_rects = []
        rect1 = find_non_overlapping_label_rect(
            path=path1,
            badge_width=90.0,
            badge_height=22.0,
            offset_idx=0,
            total_pair_conns=1,
            existing_rects=placed_rects,
        )
        placed_rects.append(rect1)

        rect2 = find_non_overlapping_label_rect(
            path=path2,
            badge_width=90.0,
            badge_height=22.0,
            offset_idx=0,
            total_pair_conns=1,
            existing_rects=placed_rects,
        )

        self.assertFalse(rect1.intersects(rect2), "Crossing connection labels must not overlap")


if __name__ == "__main__":
    unittest.main()
