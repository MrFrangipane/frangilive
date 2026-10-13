from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from frangilive.app import FrangiliveApp
from frangilive.ui.patcher.patcher_widget import PatcherWidget
from frangilive.ui.widgets import ConfirmButton


class CueWidget(QWidget):
    """
    Touch-friendly sidebar widget for managing and navigating the cue list.
    Supports creating new cues, saving current patch to cue with overwrite warning,
    deleting cues with confirmation, clearing the live patch, and stepping through cues.
    """

    cueChanged = Signal(int)
    patchChanged = Signal()

    def __init__(
        self,
        app: FrangiliveApp,
        patcher_widget: PatcherWidget | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._app = app
        self._patcher_widget = patcher_widget

        self.setMinimumWidth(220)
        self.setMaximumWidth(320)

        self._init_ui()
        self.refresh_cues()

        if self._patcher_widget is not None:
            self.patchChanged.connect(self._patcher_widget.update)
            self._patcher_widget.connectionChanged.connect(self.refresh_cues)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Title
        title_label = QLabel("CUES")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; padding: 4px;")
        main_layout.addWidget(title_label)

        # Cue List
        self._cue_list_widget = QListWidget(self)
        self._cue_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #4B5263;
                border-radius: 4px;
                background-color: #21252B;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 4px;
                margin-bottom: 2px;
            }
            QListWidget::item:selected {
                background-color: #3E4452;
                color: #61AFEF;
                font-weight: bold;
            }
        """)
        self._cue_list_widget.currentRowChanged.connect(self._on_list_row_selected)
        main_layout.addWidget(self._cue_list_widget, stretch=1)

        # Navigation buttons (First, Prev, Next)
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(4)

        self._btn_first = QPushButton("|< First", self)
        self._btn_first.setMinimumHeight(44)
        self._btn_first.clicked.connect(self.go_to_first_cue)
        nav_layout.addWidget(self._btn_first)

        self._btn_prev = QPushButton("< Prev", self)
        self._btn_prev.setMinimumHeight(44)
        self._btn_prev.clicked.connect(self.go_to_previous_cue)
        nav_layout.addWidget(self._btn_prev)

        self._btn_next = QPushButton("Next >", self)
        self._btn_next.setMinimumHeight(44)
        self._btn_next.clicked.connect(self.go_to_next_cue)
        nav_layout.addWidget(self._btn_next)

        main_layout.addLayout(nav_layout)

        # Action buttons
        self._btn_new = QPushButton("+ New Cue", self)
        self._btn_new.setMinimumHeight(44)
        self._btn_new.clicked.connect(self.create_new_cue)
        main_layout.addWidget(self._btn_new)

        self._btn_save = ConfirmButton("Save Cue", confirm_text="Overwrite ?", parent=self)
        self._btn_save.setMinimumHeight(44)
        self._btn_save.clicked.connect(self.save_current_cue)
        main_layout.addWidget(self._btn_save)

        self._btn_delete = ConfirmButton("Delete Cue", confirm_text="Delete ?", parent=self)
        self._btn_delete.setMinimumHeight(44)
        self._btn_delete.clicked.connect(self.delete_current_cue)
        main_layout.addWidget(self._btn_delete)

        self._btn_empty = ConfirmButton("Empty Patch", confirm_text="Clear ?", parent=self)
        self._btn_empty.setMinimumHeight(44)
        self._btn_empty.clicked.connect(self.empty_patch)
        main_layout.addWidget(self._btn_empty)

    def refresh_cues(self):
        """Updates cue list display and active selection."""
        self._cue_list_widget.blockSignals(True)
        self._cue_list_widget.clear()

        cue_list = self._app.cue_list
        for i, cue in enumerate(cue_list):
            item_text = f"{i + 1}. {cue.name} ({cue.connection_count()} cables)"
            item = QListWidgetItem(item_text)
            self._cue_list_widget.addItem(item)

        if cue_list.current_index is not None and 0 <= cue_list.current_index < len(cue_list):
            self._cue_list_widget.setCurrentRow(cue_list.current_index)
        else:
            self._cue_list_widget.setCurrentRow(-1)

        self._cue_list_widget.blockSignals(False)

    def _on_list_row_selected(self, row: int):
        if row < 0 or row >= len(self._app.cue_list):
            return
        if row != self._app.cue_list.current_index:
            self._app.go_to_cue(row)
            self._notify_cue_changed(row)

    def create_new_cue(self):
        """Creates a new cue from current patch and selects it."""
        cue = self._app.create_cue_from_current_patch()
        self.refresh_cues()
        if self._app.cue_list.current_index is not None:
            self._notify_cue_changed(self._app.cue_list.current_index)

    def save_current_cue(self):
        """Overwrites current active cue with live patcher connections."""
        if self._app.cue_list.current_cue is None:
            # If no cue exists yet, create one
            self.create_new_cue()
            return

        self._app.save_current_patch_to_current_cue()
        self.refresh_cues()

    def delete_current_cue(self):
        """Deletes the active cue and loads the next available cue patch."""
        if self._app.cue_list.current_cue is None:
            return

        self._app.delete_current_cue()
        self.refresh_cues()
        if self._app.cue_list.current_index is not None:
            self._notify_cue_changed(self._app.cue_list.current_index)
        else:
            self.patchChanged.emit()
            if self._patcher_widget is not None:
                self._patcher_widget.connectionChanged.emit()
                self._patcher_widget.update()

    def empty_patch(self):
        """Clears all live connections from the patcher and audio router."""
        self._app.empty_patch()
        self.patchChanged.emit()
        if self._patcher_widget is not None:
            self._patcher_widget.connectionChanged.emit()

    def go_to_first_cue(self):
        """Switches to the first cue and loads its connections."""
        cue = self._app.go_to_first_cue()
        if cue is not None and self._app.cue_list.current_index is not None:
            self.refresh_cues()
            self._notify_cue_changed(self._app.cue_list.current_index)

    def go_to_next_cue(self):
        """Switches to the next cue and loads its connections."""
        cue = self._app.go_to_next_cue()
        if cue is not None and self._app.cue_list.current_index is not None:
            self.refresh_cues()
            self._notify_cue_changed(self._app.cue_list.current_index)

    def go_to_previous_cue(self):
        """Switches to the previous cue and loads its connections."""
        cue = self._app.go_to_previous_cue()
        if cue is not None and self._app.cue_list.current_index is not None:
            self.refresh_cues()
            self._notify_cue_changed(self._app.cue_list.current_index)

    def _notify_cue_changed(self, index: int):
        self.cueChanged.emit(index)
        self.patchChanged.emit()
        if self._patcher_widget is not None:
            self._patcher_widget.connectionChanged.emit()
            self._patcher_widget.update()
