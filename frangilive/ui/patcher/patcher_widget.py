import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainterPath
from PySide6.QtWidgets import QMenu, QWidget

from frangilive.app import FrangiliveApp
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.patcher.domain.audio_connection import AudioConnection
from frangilive.ui.patcher.config import PatcherWidgetConfig
from frangilive.ui.patcher.geometry import (
    node_shape,
    stroked_path,
    trimmed_curved_path_between_shapes
)
from frangilive.ui.patcher.painter import PatcherPainterMixin
from frangilive.ui.patcher.port_selector import PortSelectorDialog


class PatcherWidget(PatcherPainterMixin, QWidget):
    """
    Circular UI for presenting audio devices and connecting them via click-and-drag.
    Supports touchscreens, long-press port selection, default port customization,
    and visual connection arrows.
    """

    connectionChanged = Signal()

    def __init__(
            self,
            app: FrangiliveApp,
            config: PatcherWidgetConfig | None = None,
            parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._app = app
        self._config = config if config is not None else PatcherWidgetConfig()
        self._patcher = app.patcher
        self._device_library = app.device_library

        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Drag & Touch state
        self._is_dragging = False
        self._drag_source_device: AudioInstrument | None = None
        self._drag_source_port: str | None = None
        self._current_drag_pos = QPointF()

        self._press_pos = QPointF()
        self._press_device: AudioInstrument | None = None
        self._hover_target_device: AudioInstrument | None = None
        self._hover_invalid_target_device: AudioInstrument | None = None

        # Timers for touch & long press (configurable)
        self._long_press_timer = QTimer(self)
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.setInterval(self._config.long_press_interval)
        self._long_press_timer.timeout.connect(self._on_start_device_long_press)

        self._hover_long_press_timer = QTimer(self)
        self._hover_long_press_timer.setSingleShot(True)
        self._hover_long_press_timer.setInterval(self._config.hover_long_press_interval)
        self._hover_long_press_timer.timeout.connect(self._on_hover_long_press)

        # Cached device node bounding rects: dict[str, QRectF]
        self._node_rects: dict[str, QRectF] = {}

    @property
    def config(self) -> PatcherWidgetConfig:
        return self._config

    @property
    def long_press_interval(self) -> int:
        return self._long_press_timer.interval()

    @long_press_interval.setter
    def long_press_interval(self, value: int):
        self._config.long_press_interval = value
        self._long_press_timer.setInterval(value)

    @property
    def hover_long_press_interval(self) -> int:
        return self._hover_long_press_timer.interval()

    @hover_long_press_interval.setter
    def hover_long_press_interval(self, value: int):
        self._config.hover_long_press_interval = value
        self._hover_long_press_timer.setInterval(value)


    def _calculate_node_rects(self) -> dict[str, QRectF]:
        """Calculates circular positions for all devices in the library."""
        rects: dict[str, QRectF] = {}
        instruments = self._device_library.audio_instruments
        n = len(instruments)
        if n == 0:
            self._node_rects = rects
            return rects

        center_x = self.width() / 2.0
        center_y = self.height() / 2.0

        margin = max(self._config.node_width, self._config.node_height) / 2.0 + self._config.node_margin_padding
        radius = max(self._config.min_layout_radius, min(self.width(), self.height()) / 2.0 - margin)

        for i, instrument in enumerate(instruments):
            angle = -math.pi / 2.0 + (2.0 * math.pi * i) / n
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            rects[instrument.name] = QRectF(
                x - self._config.node_width / 2.0,
                y - self._config.node_height / 2.0,
                self._config.node_width,
                self._config.node_height,
            )

        self._node_rects = rects
        return rects

    def _get_device_at_pos(self, pos: QPointF) -> AudioInstrument | None:
        """Finds the device node at the given position with touch padding."""
        touch_padding = self._config.node_touch_padding
        for name, rect in self._node_rects.items():
            padded_shape = node_shape(
                rect.adjusted(
                    -touch_padding,
                    -touch_padding,
                    touch_padding,
                    touch_padding,
                )
            )
            if padded_shape.contains(pos):
                return self._device_library.get_instrument(name)

        return None

    def _connection_path(
            self,
            connection: AudioConnection,
            offset_idx: int = 0,
    ) -> QPainterPath:
        """Builds the visual path for an existing connection."""
        src_rect = self._node_rects.get(connection.source_instrument.name)
        tgt_rect = self._node_rects.get(connection.target_instrument.name)
        if not src_rect or not tgt_rect:
            return QPainterPath()

        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        return trimmed_curved_path_between_shapes(
            start_shape=node_shape(src_rect),
            start_center=src_rect.center(),
            end_shape=node_shape(tgt_rect),
            end_point=tgt_rect.center(),
            center=center,
            curvature=self._config.wire_curvature,
            offset_idx=offset_idx,
            curvature_offset=self._config.wire_curvature_offset,
        )

    def _get_connection_at_pos(
            self,
            pos: QPointF,
            threshold: float | None = None,
    ) -> AudioConnection | None:
        """Finds an existing connection arrow near pos."""
        hit_threshold = threshold if threshold is not None else self._config.connection_hit_threshold
        drawn_pairs: dict[tuple[str, str], int] = {}
        for conn in self._patcher.connections:
            pair = (conn.source_instrument.name, conn.target_instrument.name)
            offset_idx = drawn_pairs.get(pair, 0)
            drawn_pairs[pair] = offset_idx + 1

            cable_path = self._connection_path(conn, offset_idx=offset_idx)
            if cable_path.isEmpty():
                continue

            if stroked_path(cable_path, hit_threshold * 2.0).contains(pos):
                return conn

        return None

    def _is_target_valid_for_connection(
            self,
            source: AudioInstrument,
            target: AudioInstrument,
    ) -> bool:
        """Checks whether target has available inputs and connecting source->target is acyclic."""
        if not target.inputs:
            return False
        if source.name == target.name:
            return False
        return not self._patcher.would_create_cycle_between(source.name, target.name)

    def _drag_path(self, node_rects: dict[str, QRectF]) -> QPainterPath:
        """Builds the visual path for the current drag connection."""
        if not self._drag_source_device:
            return QPainterPath()

        src_rect = node_rects.get(self._drag_source_device.name)
        if not src_rect:
            return QPainterPath()

        target_shape = None
        target_point = self._current_drag_pos

        target_device = self._hover_target_device or self._hover_invalid_target_device
        if target_device:
            tgt_rect = node_rects.get(target_device.name)
            if tgt_rect:
                target_shape = node_shape(tgt_rect)
                target_point = tgt_rect.center()

        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        return trimmed_curved_path_between_shapes(
            start_shape=node_shape(src_rect),
            start_center=src_rect.center(),
            end_shape=target_shape,
            end_point=target_point,
            center=center,
            curvature=self._config.wire_curvature,
        )

    # -------------------------------------------------------------------------
    # Touch & Mouse Event Handlers
    # -------------------------------------------------------------------------

    def _cancel_drag(self):
        """Cancels any in-progress dragging or pending long-press interactions."""
        self._long_press_timer.stop()
        self._hover_long_press_timer.stop()
        self._is_dragging = False
        self._drag_source_device = None
        self._drag_source_port = None
        self._hover_target_device = None
        self._hover_invalid_target_device = None
        self._press_device = None
        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape and self._is_dragging:
            self._cancel_drag()
            return

        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._handle_press(event.position())
        elif event.button() == Qt.RightButton:
            self._handle_right_click(event.position())

    def mouseMoveEvent(self, event: QMouseEvent):
        self._handle_move(event.position())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._handle_release(event.position())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            device = self._get_device_at_pos(event.position())
            if device:
                self._show_device_config(device)

    def _handle_press(self, pos: QPointF):
        device = self._get_device_at_pos(pos)
        self._press_pos = pos

        if device:
            self._press_device = device
            self._long_press_timer.start()
        else:
            self._press_device = None
            conn = self._get_connection_at_pos(pos)
            if conn:
                self._disconnect_connection(conn)

        self.update()

    def _handle_move(self, pos: QPointF):
        if self._press_device and not self._is_dragging:
            dist = math.hypot(
                pos.x() - self._press_pos.x(),
                pos.y() - self._press_pos.y(),
                )
            if dist > self._config.drag_threshold:
                self._long_press_timer.stop()
                if self._press_device.outputs:
                    self._is_dragging = True
                    self._drag_source_device = self._press_device
                    default_out = self._press_device.get_default_output()
                    self._drag_source_port = default_out.name if default_out else None
                    self._current_drag_pos = pos

        if self._is_dragging:
            self._current_drag_pos = pos
            target_device = self._get_device_at_pos(pos)

            if target_device and target_device != self._drag_source_device:
                if self._is_target_valid_for_connection(self._drag_source_device, target_device):
                    self._hover_target_device = target_device
                    self._hover_invalid_target_device = None
                    self._hover_long_press_timer.start()
                else:
                    self._hover_target_device = None
                    self._hover_invalid_target_device = target_device
                    self._hover_long_press_timer.stop()
            else:
                self._hover_target_device = None
                self._hover_invalid_target_device = None
                self._hover_long_press_timer.stop()

            self.update()

    def _handle_release(self, pos: QPointF):
        self._long_press_timer.stop()
        self._hover_long_press_timer.stop()

        if self._is_dragging:
            target_device = self._get_device_at_pos(pos)
            if (
                    target_device
                    and target_device != self._drag_source_device
                    and self._drag_source_device
                    and self._drag_source_port
                    and self._is_target_valid_for_connection(self._drag_source_device, target_device)
            ):
                default_in = target_device.get_default_input()
                target_port = default_in.name if default_in else None
                if target_port:
                    self._connect_devices(
                        self._drag_source_device,
                        self._drag_source_port,
                        target_device,
                        target_port,
                    )

            self._cancel_drag()
        else:
            self._press_device = None
            self.update()

    def _handle_right_click(self, pos: QPointF):
        device = self._get_device_at_pos(pos)
        if device:
            self._show_device_config(device)
            return

        conn = self._get_connection_at_pos(pos)
        if conn:
            self._disconnect_connection(conn)

    # -------------------------------------------------------------------------
    # Long Press Actions / Port Selection
    # -------------------------------------------------------------------------

    def _on_start_device_long_press(self):
        """Triggered on long press over start device: allows output port selection then sets drag mode."""
        self._long_press_timer.stop()
        if not self._press_device:
            return

        device = self._press_device

        if device.outputs:
            if len(device.outputs) == 1:
                self._drag_source_device = device
                self._drag_source_port = device.outputs[0].name
                self._is_dragging = True
                self._current_drag_pos = self._press_pos
                self.update()
                return

            port_names = [p.name for p in device.outputs]
            default_out = device.get_default_output()
            current_default = default_out.name if default_out else None

            dialog = PortSelectorDialog(
                instrument_name=device.name,
                port_names=port_names,
                current_default=current_default,
                is_output=True,
                config=self._config,
                parent=self,
            )
            if dialog.exec() and dialog.selected_port:
                self._drag_source_device = device
                self._drag_source_port = dialog.selected_port
                self._is_dragging = True
                self._current_drag_pos = self._press_pos
                self.update()
            else:
                self._cancel_drag()
        else:
            self._cancel_drag()

    def _on_hover_long_press(self):
        """Triggered when staying long over a device while dragging: allows in port selection then connects."""
        self._hover_long_press_timer.stop()
        if not self._is_dragging or not self._hover_target_device or not self._drag_source_device:
            return

        target_device = self._hover_target_device
        source_device = self._drag_source_device
        source_port = self._drag_source_port

        if not self._is_target_valid_for_connection(source_device, target_device) or not source_port:
            self._cancel_drag()
            return

        if len(target_device.inputs) == 1:
            self._connect_devices(
                source_device,
                source_port,
                target_device,
                target_device.inputs[0].name,
            )
            self._cancel_drag()
            return

        port_names = [p.name for p in target_device.inputs]
        default_in = target_device.get_default_input()
        current_default = default_in.name if default_in else None

        dialog = PortSelectorDialog(
            instrument_name=target_device.name,
            port_names=port_names,
            current_default=current_default,
            is_output=False,
            config=self._config,
            parent=self,
        )

        if dialog.exec() and dialog.selected_port:
            self._connect_devices(
                source_device,
                source_port,
                target_device,
                dialog.selected_port,
            )

        self._cancel_drag()

    def _show_device_config(self, device: AudioInstrument):
        """Opens port selection menu to customize default input or output."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #21252B;
                color: #ECEFF4;
                border: 1px solid #4B5263;
                font-size: 13px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3E4452;
                color: #61AFEF;
            }
        """)

        menu.addSection(f"{device.name} Ports")

        if len(device.outputs) > 1:
            default_output = device.get_default_output()
            output_name = default_output.name if default_output else "None"
            out_action = menu.addAction(f"Select Default Output ({output_name})")
            out_action.triggered.connect(
                lambda: self._select_default_port(device, is_output=True)
            )

        if len(device.inputs) > 1:
            default_input = device.get_default_input()
            input_name = default_input.name if default_input else "None"
            in_action = menu.addAction(f"Select Default Input ({input_name})")
            in_action.triggered.connect(
                lambda: self._select_default_port(device, is_output=False)
            )

        dev_conns = [
            c for c in self._patcher.connections
            if c.source_instrument == device or c.target_instrument == device
        ]
        if dev_conns:
            menu.addSeparator()
            disc_action = menu.addAction(f"Disconnect All ({len(dev_conns)} connections)")
            disc_action.triggered.connect(
                lambda: self._disconnect_device_connections(device)
            )

        menu.exec(
            self.mapToGlobal(
                self._node_rects.get(device.name, QRectF()).center().toPoint()
            )
        )

    def _select_default_port(self, device: AudioInstrument, is_output: bool):
        port_list = device.outputs if is_output else device.inputs
        if len(port_list) <= 1:
            if len(port_list) == 1:
                if is_output:
                    device.set_default_output(port_list[0].name)
                else:
                    device.set_default_input(port_list[0].name)
            return

        default_port = device.get_default_output() if is_output else device.get_default_input()
        dialog = PortSelectorDialog(
            instrument_name=device.name,
            port_names=[p.name for p in port_list],
            current_default=default_port.name if default_port else None,
            is_output=is_output,
            config=self._config,
            parent=self,
        )

        if dialog.exec() and dialog.selected_port:
            if is_output:
                device.set_default_output(dialog.selected_port)
            else:
                device.set_default_input(dialog.selected_port)

            self.update()

    def _connect_devices(
            self,
            source: AudioInstrument,
            source_port: str,
            target: AudioInstrument,
            target_port: str,
    ):
        success = self._app.connect(source.name, source_port, target.name, target_port)
        if success:
            self.connectionChanged.emit()

        self.update()

    def _disconnect_connection(self, connection: AudioConnection):
        self._app.disconnect(
            connection.source_instrument.name,
            connection.source_port.name,
            connection.target_instrument.name,
            connection.target_port.name,
        )
        self.connectionChanged.emit()
        self.update()

    def _disconnect_device_connections(self, device: AudioInstrument):
        to_disconnect = [
            c for c in list(self._patcher.connections)
            if c.source_instrument == device or c.target_instrument == device
        ]
        for conn in to_disconnect:
            self._disconnect_connection(conn)
