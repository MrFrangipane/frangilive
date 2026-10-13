import math
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QSizePolicy
)

from frangilive.ui.patcher.config import PatcherWidgetConfig


class PortSelectorDialog(QDialog):
    """
    Touch-friendly dialog for selecting an input or output port of an audio instrument.
    Lays out buttons in at most max_rows rows across dynamic columns for optimal touch ergonomics.
    """

    def __init__(
        self,
        instrument_name: str,
        port_names: list[str],
        current_default: str | None = None,
        is_output: bool = True,
        config: PatcherWidgetConfig | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config if config is not None else PatcherWidgetConfig()
        self.setWindowTitle(f"Select {'Output' if is_output else 'Input'} Port")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self._selected_port: str | None = None

        self.setStyleSheet("""
            QDialog {
                background-color: #21252B;
                border: 2px solid #61AFEF;
                border-radius: 12px;
            }
            QLabel#title {
                color: #ECEFF4;
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }
            QLabel#subtitle {
                color: #ABB2BF;
                font-size: 12px;
                padding-bottom: 4px;
            }
            QPushButton.port-btn {
                background-color: #2C313A;
                color: #ECEFF4;
                border: 1px solid #4B5263;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                min-height: 42px;
                text-align: center;
            }
            QPushButton.port-btn:hover, QPushButton.port-btn:pressed {
                background-color: #3E4452;
                border-color: #61AFEF;
            }
            QPushButton.port-btn-default {
                background-color: #2D3748;
                border: 2px solid #98C379;
                color: #98C379;
                font-weight: bold;
            }
            QPushButton#cancel-btn {
                background-color: #E06C75;
                color: #FFFFFF;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                min-height: 38px;
                font-weight: bold;
            }
            QPushButton#cancel-btn:hover {
                background-color: #BE5046;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self._config.port_selector_layout_margin_left,
            self._config.port_selector_layout_margin_top,
            self._config.port_selector_layout_margin_right,
            self._config.port_selector_layout_margin_bottom,
        )
        layout.setSpacing(self._config.port_selector_layout_spacing)

        # Header
        title_type = "Output" if is_output else "Input"
        title_label = QLabel(f"{instrument_name} — Select {title_type} Port", self)
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        sub_label = QLabel("Tap a port to select", self)
        sub_label.setObjectName("subtitle")
        sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub_label)

        # Scroll area for ports
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        grid = QGridLayout(container)
        grid.setSpacing(self._config.port_selector_grid_spacing)
        grid.setContentsMargins(
            self._config.port_selector_grid_margin,
            self._config.port_selector_grid_margin,
            self._config.port_selector_grid_margin,
            self._config.port_selector_grid_margin,
        )

        # Ensure at most max_rows button rows max
        max_rows = self._config.port_selector_max_rows
        num_ports = len(port_names)
        cols = max(1, math.ceil(num_ports / max_rows)) if num_ports > 0 else 1

        for idx, port_name in enumerate(port_names):
            btn = QPushButton(port_name, container)
            btn.setProperty("class", "port-btn")
            if port_name == current_default:
                btn.setProperty("class", "port-btn port-btn-default")
                btn.setText(f"★ {port_name}")

            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(lambda checked=False, p=port_name: self._on_port_clicked(p))
            row = idx // cols
            col = idx % cols
            grid.addWidget(btn, row, col)

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        # Cancel button
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.setObjectName("cancel-btn")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        # Sizing: wider window to fit grid with max rows
        base_col_width = self._config.port_selector_base_col_width
        computed_width = max(
            self._config.port_selector_min_width,
            cols * base_col_width + self._config.port_selector_width_padding,
        )
        if parent and hasattr(parent, "width") and parent.width() > 200:
            computed_width = min(
                computed_width,
                max(self._config.port_selector_min_width, parent.width() - self._config.port_selector_parent_margin),
            )

        actual_rows = min(max_rows, math.ceil(num_ports / cols)) if num_ports > 0 else 1
        computed_height = self._config.port_selector_base_height + actual_rows * self._config.port_selector_row_height

        self.setMinimumWidth(computed_width)
        self.setMaximumWidth(min(self._config.port_selector_max_width, computed_width + self._config.port_selector_extra_width))
        self.setMinimumHeight(min(self._config.port_selector_max_height, computed_height))
        self.adjustSize()

    def _on_port_clicked(self, port_name: str):
        self._selected_port = port_name
        self.accept()

    @property
    def selected_port(self) -> str | None:
        return self._selected_port
