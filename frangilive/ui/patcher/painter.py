import math
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QBrush,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)

from frangilive.ui.patcher.geometry import (
    MIN_CABLE_LENGTH,
    find_non_overlapping_label_rect,
    node_shape,
    path_end_tangent_angle,
    path_endpoints,
    path_midpoint,
)

if TYPE_CHECKING:
    from frangilive.patcher.domain.audio_connection import AudioConnection


class PatcherPainterMixin:
    """Painting and rendering behavior for PatcherWidget."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        painter.fillRect(self.rect(), QColor(self._config.background_color))

        node_rects = self._calculate_node_rects()

        self._draw_background_circle(painter)
        self._draw_connection_arrows(painter, node_rects)

        if self._is_dragging and self._drag_source_device:
            self._draw_drag_arrow(painter, node_rects)

        self._draw_device_nodes(painter, node_rects)
        self._draw_info_hint(painter)

        painter.end()

    def _draw_background_circle(self, painter: QPainter):
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        margin = max(self._config.node_width, self._config.node_height) / 2.0 + self._config.node_margin_padding
        radius = max(self._config.min_layout_radius, min(self.width(), self.height()) / 2.0 - margin)

        pen = QPen(QColor(*self._config.background_circle_color))
        pen.setWidth(self._config.background_circle_width)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

    def _draw_connection_arrows(self, painter: QPainter, node_rects: dict[str, QRectF]):
        """Draws directed arrows for all active connections in patcher."""
        pair_counts: dict[tuple[str, str], int] = {}
        for conn in self._patcher.connections:
            pair = (conn.source_instrument.name, conn.target_instrument.name)
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

        drawn_pairs: dict[tuple[str, str], int] = {}
        placed_label_rects: list[QRectF] = []
        obstacle_rects: list[QRectF] = list(node_rects.values())

        arrows_to_draw = []

        for conn in self._patcher.connections:
            src_inst = conn.source_instrument
            tgt_inst = conn.target_instrument
            src_name = src_inst.name
            tgt_name = tgt_inst.name

            if src_name not in node_rects or tgt_name not in node_rects:
                continue

            pair = (src_name, tgt_name)
            offset_idx = drawn_pairs.get(pair, 0)
            drawn_pairs[pair] = offset_idx + 1
            total_pair_conns = pair_counts.get(pair, 1)

            cable_path = self._connection_path(conn, offset_idx=offset_idx)
            if cable_path.isEmpty():
                continue

            cable_color = (
                QColor(self._config.primary_cable_color)
                if offset_idx == 0
                else QColor(self._config.secondary_cable_color)
            )
            has_multiple_ports = (
                len(src_inst.outputs) > 1
                or len(tgt_inst.inputs) > 1
                or total_pair_conns > 1
            )
            wire_label = (
                f"{conn.source_port.name} → {conn.target_port.name}"
                if has_multiple_ports
                else ""
            )

            arrows_to_draw.append({
                "path": cable_path,
                "color": cable_color,
                "label": wire_label,
                "offset_idx": offset_idx,
                "total_pair_conns": total_pair_conns,
            })

        for item in arrows_to_draw:
            self._draw_arrow(
                painter,
                path=item["path"],
                color=item["color"],
                line_width=self._config.connection_line_width,
                arrow_size=self._config.connection_arrow_size,
            )

        for item in arrows_to_draw:
            if item["label"]:
                self._draw_wire_label(
                    painter,
                    path=item["path"],
                    label=item["label"],
                    offset_idx=item["offset_idx"],
                    total_pair_conns=item["total_pair_conns"],
                    existing_rects=placed_label_rects,
                    obstacle_rects=obstacle_rects,
                )

    def _draw_drag_arrow(self, painter: QPainter, node_rects: dict[str, QRectF]):
        """Draws the dynamic arrow while dragging."""
        drag_path = self._drag_path(node_rects)
        if drag_path.isEmpty():
            return

        drag_color = (
            QColor(self._config.drag_cable_color)
            if not self._hover_target_device
            else QColor(self._config.drag_hover_cable_color)
        )

        self._draw_arrow(
            painter,
            path=drag_path,
            color=drag_color,
            line_width=self._config.drag_line_width,
            arrow_size=self._config.drag_arrow_size,
            dashed=True,
            label=f"Out: {self._drag_source_port}" if self._drag_source_port else "",
        )

    def _draw_arrow(
            self,
            painter: QPainter,
            path: QPainterPath,
            color: QColor,
            line_width: float = 3.0,
            arrow_size: float = 12.0,
            dashed: bool = False,
            label: str = "",
    ):
        if path.isEmpty() or path.length() < MIN_CABLE_LENGTH:
            return

        angle = path_end_tangent_angle(path)
        p_end = path.pointAtPercent(1.0)

        pen = QPen(color)
        pen.setWidthF(line_width)
        pen.setCapStyle(Qt.RoundCap)
        if dashed:
            pen.setStyle(Qt.DashLine)

        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        head_angle = math.pi / self._config.arrow_head_angle_divisor
        p_wing1 = QPointF(
            p_end.x() - arrow_size * math.cos(angle - head_angle),
            p_end.y() - arrow_size * math.sin(angle - head_angle),
        )
        p_wing2 = QPointF(
            p_end.x() - arrow_size * math.cos(angle + head_angle),
            p_end.y() - arrow_size * math.sin(angle + head_angle),
        )

        polygon = QPolygonF([p_end, p_wing1, p_wing2])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(polygon)

        if label:
            self._draw_wire_label(painter, path, label)

    def _draw_wire_label(
            self,
            painter: QPainter,
            path: QPainterPath,
            label: str,
            offset_idx: int = 0,
            total_pair_conns: int = 1,
            existing_rects: list[QRectF] | None = None,
            obstacle_rects: list[QRectF] | None = None,
    ):
        """Draws a readable label badge on the path, positioned to avoid overlaps."""
        font = QFont(painter.font())
        font.setPointSize(self._config.wire_label_font_size)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(label) + self._config.wire_label_horizontal_padding
        text_h = fm.height() + self._config.wire_label_vertical_padding

        badge_rect = find_non_overlapping_label_rect(
            path=path,
            badge_width=text_w,
            badge_height=text_h,
            offset_idx=offset_idx,
            total_pair_conns=total_pair_conns,
            existing_rects=existing_rects,
            obstacle_rects=obstacle_rects,
            padding=self._config.wire_label_padding,
        )

        if existing_rects is not None:
            existing_rects.append(badge_rect)

        painter.setPen(
            QPen(
                QColor(self._config.wire_label_border_color),
                self._config.wire_label_border_width,
            )
        )
        painter.setBrush(QBrush(QColor(*self._config.wire_label_background_rgba)))
        painter.drawRoundedRect(
            badge_rect,
            self._config.wire_label_radius,
            self._config.wire_label_radius,
        )

        painter.setPen(QColor(self._config.wire_label_text_color))
        painter.drawText(badge_rect, Qt.AlignCenter, label)

    def _draw_device_nodes(self, painter: QPainter, node_rects: dict[str, QRectF]):
        """Draws each audio instrument node with title, default ports, and status highlights."""
        for instrument in self._device_library.audio_instruments:
            rect = node_rects.get(instrument.name)
            if not rect:
                continue

            is_pressed = self._press_device == instrument and not self._is_dragging
            is_drag_source = self._is_dragging and self._drag_source_device == instrument
            is_hover_target = self._is_dragging and self._hover_target_device == instrument
            has_connections = any(
                c.source_instrument == instrument or c.target_instrument == instrument
                for c in self._patcher.connections
            )

            bg_color = QColor(self._config.node_background_color)
            border_color = QColor(self._config.node_border_color)
            border_width = self._config.node_border_width

            if is_hover_target:
                border_color = QColor(self._config.node_hover_border_color)
                border_width = self._config.node_hover_border_width
                bg_color = QColor(self._config.node_hover_background_color)
            elif is_drag_source:
                border_color = QColor(self._config.node_drag_border_color)
                border_width = self._config.node_drag_border_width
                bg_color = QColor(self._config.node_drag_background_color)
            elif is_pressed:
                border_color = QColor(self._config.node_pressed_border_color)
                border_width = self._config.node_pressed_border_width
                bg_color = QColor(self._config.node_pressed_background_color)
            elif has_connections:
                border_color = QColor(self._config.node_connected_border_color)
                border_width = self._config.node_connected_border_width

            painter.setPen(QPen(border_color, border_width))
            painter.setBrush(QBrush(bg_color))
            painter.drawPath(node_shape(rect))

            painter.setPen(
                QColor(
                    self._config.node_active_text_color
                    if is_drag_source or is_hover_target
                    else self._config.node_text_color
                )
            )
            font = QFont(self.font())
            font.setBold(True)
            font.setPointSize(self._config.node_name_font_size)
            painter.setFont(font)

            name_rect = QRectF(
                rect.x() + self._config.node_name_rect_x_padding,
                rect.y() + self._config.node_name_rect_y_padding,
                rect.width() - (2 * self._config.node_name_rect_x_padding),
                self._config.node_name_rect_height,
            )
            painter.drawText(name_rect, Qt.AlignCenter, instrument.name)

            font.setBold(False)
            font.setPointSize(self._config.node_port_font_size)
            painter.setFont(font)

            def_out = instrument.get_default_output()
            def_in = instrument.get_default_input()

            port_info = []
            if def_out:
                port_info.append(f"Out: {def_out.name}")
            if def_in:
                port_info.append(f"In: {def_in.name}")

            port_text = " | ".join(port_info) if port_info else "No ports"

            painter.setPen(
                QColor(
                    self._config.node_output_port_color
                    if def_out
                    else self._config.node_no_output_port_color
                )
            )
            port_rect = QRectF(
                rect.x() + self._config.node_port_rect_x_padding,
                rect.y() + self._config.node_port_rect_y,
                rect.width() - (2 * self._config.node_port_rect_x_padding),
                self._config.node_port_rect_height,
            )
            painter.drawText(port_rect, Qt.AlignCenter, port_text)

    def _draw_info_hint(self, painter: QPainter):
        """Displays subtle hint or connection count in center."""
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0

        conns_count = len(self._patcher.connections)
        hint_text = f"{conns_count} Active Cable{'s' if conns_count != 1 else ''}"

        font = QFont(self.font())
        font.setPointSize(self._config.info_font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(*self._config.info_text_rgba))

        info_rect = QRectF(
            center_x - self._config.info_rect_width / 2.0,
            center_y - self._config.info_rect_height / 2.0,
            self._config.info_rect_width,
            self._config.info_rect_height,
        )
        painter.drawText(info_rect, Qt.AlignCenter, hint_text)
