import math
import re
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
    QImage,
)
from PySide6.QtSvg import QSvgRenderer

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
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        painter.fillRect(self.rect(), QColor(self._config.background_color))

        node_rects = self._calculate_node_rects()

        self._draw_background_circle(painter)
        self._draw_device_nodes(painter, node_rects)

        self._draw_connection_arrows(painter, node_rects)

        if self._is_dragging and self._drag_source_device:
            self._draw_drag_arrow(painter, node_rects)

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

    def _format_aggregated_connection_label(self, connections: list["AudioConnection"]) -> str:
        """
        Formats a combined badge label for connections between the same pair of devices.
        Aggregates track/port ranges (e.g., 'Tracks 2–4') or multiline/cable count.
        Omits port names when a device only has one port of that kind (input or output).
        """
        if not connections:
            return ""

        src_inst = connections[0].source_instrument
        tgt_inst = connections[0].target_instrument

        # If there's only one connection, and it's a default->default connection, skip the label
        if len(connections) == 1:
            c = connections[0]
            is_src_default = c.source_port == c.source_instrument.get_default_output()
            is_tgt_default = c.target_port == c.target_instrument.get_default_input()
            if is_src_default and is_tgt_default:
                return ""

        src_has_multiple = len(src_inst.outputs) > 1
        tgt_has_multiple = len(tgt_inst.inputs) > 1

        if not src_has_multiple and not tgt_has_multiple:
            return "" if len(connections) == 1 else f"{len(connections)} Cables"

        if len(connections) == 1:
            conn = connections[0]
            if src_has_multiple and tgt_has_multiple:
                return f"{conn.source_port.name} → {conn.target_port.name}"
            elif src_has_multiple:
                return f"{conn.source_port.name} →"
            else:
                return f"→ {conn.target_port.name}"

        src_ports = [c.source_port.name for c in connections]
        tgt_ports = [c.target_port.name for c in connections]

        def _summarize_ports(ports: list[str]) -> str:
            if not ports:
                return ""
            if len(ports) == 1:
                return ports[0]
            if all(p == ports[0] for p in ports):
                return ports[0]

            pattern = re.compile(r"^([A-Za-z\s_-]*?)(\d+)(.*)$")
            matches = [pattern.match(p) for p in ports]
            if all(m is not None for m in matches):
                prefixes = [m.group(1) for m in matches]  # type: ignore
                suffixes = [m.group(3) for m in matches]  # type: ignore
                if len(set(prefixes)) == 1 and len(set(suffixes)) == 1:
                    prefix = prefixes[0]
                    suffix = suffixes[0]
                    nums = [int(m.group(2)) for m in matches]  # type: ignore
                    min_n, max_n = min(nums), max(nums)
                    if nums == list(range(min_n, max_n + 1)) and len(nums) >= 2:
                        clean_prefix = prefix.strip()
                        if clean_prefix.lower() in ("track", "tr"):
                            prefix_display = "Tracks "
                        elif clean_prefix.lower() == "output":
                            prefix_display = "Outputs "
                        elif clean_prefix.lower() == "out":
                            prefix_display = "Out "
                        elif clean_prefix.lower() == "input":
                            prefix_display = "Inputs "
                        elif clean_prefix.lower() == "in":
                            prefix_display = "In "
                        elif clean_prefix.lower() == "port":
                            prefix_display = "Ports "
                        elif clean_prefix.lower() == "channel":
                            prefix_display = "Channels "
                        elif clean_prefix.lower() == "ch":
                            prefix_display = "Ch "
                        else:
                            prefix_display = prefix
                        return f"{prefix_display}{min_n}–{max_n}{suffix}"

                    clean_prefix = prefix.strip()
                    if clean_prefix.lower() in ("track", "tr"):
                        prefix_display = "Tracks "
                    else:
                        prefix_display = prefix
                    nums_str = ", ".join(str(n) for n in nums)
                    return f"{prefix_display}{nums_str}{suffix}"

            if len(ports) == 2 and ports[0].startswith("Main ") and ports[1].startswith("Main "):
                p0_s = ports[0][5:]
                p1_s = ports[1][5:]
                return f"Main {p0_s}/{p1_s}"

            return ", ".join(ports)

        src_summary = _summarize_ports(src_ports)
        tgt_summary = _summarize_ports(tgt_ports)

        if src_has_multiple and not tgt_has_multiple:
            if ("," not in src_summary or len(src_ports) <= 2) or "–" in src_summary or "/" in src_summary:
                return f"{src_summary} →"
            if len(connections) <= 3:
                return "\n".join(f"{c.source_port.name} →" for c in connections)
            return f"{len(connections)} Cables"

        if not src_has_multiple and tgt_has_multiple:
            if ("," not in tgt_summary or len(tgt_ports) <= 2) or "–" in tgt_summary or "/" in tgt_summary:
                return f"→ {tgt_summary}"
            if len(connections) <= 3:
                return "\n".join(f"→ {c.target_port.name}" for c in connections)
            return f"{len(connections)} Cables"

        if all(tp == tgt_ports[0] for tp in tgt_ports):
            return f"{src_summary} → {tgt_ports[0]}"

        if all(sp == src_ports[0] for sp in src_ports):
            return f"{src_ports[0]} → {tgt_summary}"

        if ("," not in src_summary or len(src_ports) <= 2) and ("," not in tgt_summary or len(tgt_ports) <= 2):
            if "–" in src_summary or "–" in tgt_summary or "/" in src_summary or "/" in tgt_summary:
                return f"{src_summary} → {tgt_summary}"

        if len(connections) <= 3:
            return "\n".join(f"{c.source_port.name} → {c.target_port.name}" for c in connections)

        return f"{len(connections)} Cables"

    def _draw_connection_arrows(self, painter: QPainter, node_rects: dict[str, QRectF]):
        """Draws directed arrows for all active connections in patcher."""
        pair_connections: dict[tuple[str, str], list["AudioConnection"]] = {}
        for conn in self._patcher.connections:
            src_name = conn.source_instrument.name
            tgt_name = conn.target_instrument.name
            if src_name not in node_rects or tgt_name not in node_rects:
                continue
            # Use undirected pair to group connections that would otherwise overlap
            # (e.g. A->B and B->A will have different curvatures)
            pair = tuple(sorted((src_name, tgt_name)))
            pair_connections.setdefault(pair, []).append(conn)

        placed_label_rects: list[QRectF] = []
        obstacle_rects: list[QRectF] = list(node_rects.values())
        all_cable_paths: list[QPainterPath] = []
        pair_bundles = []

        for pair, conns in pair_connections.items():
            cable_items = []
            for offset_idx, conn in enumerate(conns):
                cable_path = self._connection_path(conn, offset_idx=offset_idx)
                if cable_path.isEmpty():
                    continue

                all_cable_paths.append(cable_path)
                cable_color = (
                    QColor(self._config.primary_cable_color)
                    if offset_idx == 0
                    else QColor(self._config.secondary_cable_color)
                )

                cable_items.append({
                    "conn": conn,
                    "path": cable_path,
                    "color": cable_color,
                    "offset_idx": offset_idx,
                })

            if not cable_items:
                continue

            for item in cable_items:
                self._draw_arrow(
                    painter,
                    path=item["path"],
                    color=item["color"],
                    line_width=self._config.connection_line_width,
                    arrow_size=self._config.connection_arrow_size,
                )

            combined_label = self._format_aggregated_connection_label(conns)
            if combined_label:
                anchor_idx = len(cable_items) // 2
                anchor_path = cable_items[anchor_idx]["path"]
                pair_bundles.append({
                    "path": anchor_path,
                    "label": combined_label,
                    "bundle_paths": [item["path"] for item in cable_items],
                })

        # Spreading identical labels and avoiding cable crossings
        text_totals = {}
        for b in pair_bundles:
            text_totals[b["label"]] = text_totals.get(b["label"], 0) + 1

        text_counts = {}
        for bundle in pair_bundles:
            label_text = bundle["label"]
            occurrence = text_counts.get(label_text, 0)
            text_counts[label_text] = occurrence + 1

            # Obstacles are all cables except those in this bundle
            bundle_paths_ids = {id(p) for p in bundle["bundle_paths"]}
            other_cables = [p for p in all_cable_paths if id(p) not in bundle_paths_ids]

            self._draw_wire_label(
                painter,
                path=bundle["path"],
                label=label_text,
                offset_idx=occurrence,
                total_pair_conns=text_totals[label_text],
                existing_rects=placed_label_rects,
                obstacle_rects=obstacle_rects,
                obstacle_paths=other_cables,
            )

    def _draw_drag_arrow(self, painter: QPainter, node_rects: dict[str, QRectF]):
        """Draws the dynamic arrow while dragging."""
        drag_path = self._drag_path(node_rects)
        if drag_path.isEmpty():
            return

        if getattr(self, "_hover_invalid_target_device", None):
            drag_color = QColor(self._config.drag_invalid_hover_cable_color)
        elif self._hover_target_device:
            drag_color = QColor(self._config.drag_hover_cable_color)
        else:
            drag_color = QColor(self._config.drag_cable_color)

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

        # 2. Draw Wire
        pen = QPen(color)
        pen.setWidthF(line_width)
        pen.setCapStyle(Qt.RoundCap)
        if dashed:
            pen.setStyle(Qt.DashLine)

        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # 3. Draw Arrow Head
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
            obstacle_paths: list[QPainterPath] | None = None,
    ):
        """Draws a readable label badge on the path, positioned to avoid overlaps."""
        font = QFont(painter.font())
        font.setPointSize(self._config.wire_label_font_size)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        lines = label.split("\n")
        max_line_w = max(fm.horizontalAdvance(line) for line in lines)
        text_w = max_line_w + self._config.wire_label_horizontal_padding
        text_h = (len(lines) * fm.height()) + self._config.wire_label_vertical_padding

        badge_rect = find_non_overlapping_label_rect(
            path=path,
            badge_width=text_w,
            badge_height=text_h,
            offset_idx=offset_idx,
            total_pair_conns=total_pair_conns,
            existing_rects=existing_rects,
            obstacle_rects=obstacle_rects,
            obstacle_paths=obstacle_paths,
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
        """Draws each audio instrument node with title, icon, and status highlights."""
        for instrument in self._device_library.audio_instruments:
            rect = node_rects.get(instrument.name)
            if not rect:
                continue

            is_pressed = self._press_device == instrument and not self._is_dragging
            is_drag_source = self._is_dragging and self._drag_source_device == instrument
            is_hover_target = self._is_dragging and self._hover_target_device == instrument
            is_invalid_hover_target = (
                self._is_dragging
                and getattr(self, "_hover_invalid_target_device", None) == instrument
            )
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
            elif is_invalid_hover_target:
                border_color = QColor(self._config.node_invalid_hover_border_color)
                border_width = self._config.node_invalid_hover_border_width
                bg_color = QColor(self._config.node_invalid_hover_background_color)
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
                    if is_drag_source or is_hover_target or is_invalid_hover_target
                    else self._config.node_text_color
                )
            )
            font = QFont(self.font())
            font.setBold(True)
            font.setPointSize(self._config.node_name_font_size)
            painter.setFont(font)

            icon = self._icons.get(instrument.name)
            name_rect = QRectF(
                rect.x() + self._config.node_name_rect_x_padding,
                rect.y() + self._config.node_name_rect_y_padding,
                rect.width() - (2 * self._config.node_name_rect_x_padding),
                self._config.node_name_rect_height,
            )
            painter.drawText(name_rect, Qt.AlignCenter, instrument.name)

            if icon:
                icon_size = self._config.node_icon_size * self._config.node_icon_scale
                icon_rect = QRectF(
                    rect.x() + (rect.width() - icon_size) / 2.0,
                    name_rect.bottom() + self._config.node_icon_padding,
                    icon_size,
                    icon_size,
                )
                if isinstance(icon, QSvgRenderer):
                    icon.render(painter, icon_rect)
                elif isinstance(icon, QImage):
                    painter.drawImage(icon_rect, icon)
                elif hasattr(icon, "render"):
                    icon.render(painter, icon_rect)
