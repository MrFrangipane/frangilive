from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton

from pyside6helpers.layout import clear

from frangilive.ui.patcher.make_button import make_button


class PortsWidget(QWidget):

    changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(QGridLayout())

        self._buttons: list[QPushButton] = []

    def set_port_names(self, port_names: list[str]):
        self.setVisible(len(port_names) > 0)

        layout: QGridLayout = self.layout()
        clear(layout)
        self._buttons = []

        for row, port_name in enumerate(port_names):
            button = make_button(port_name)
            button.clicked.connect(self._emit_changed)
            self._buttons.append(button)
            layout.addWidget(button, row, 0)

        self._emit_changed()

    def _emit_changed(self):
        self.changed.emit([button.text() for button in self._buttons if button.isChecked()])

