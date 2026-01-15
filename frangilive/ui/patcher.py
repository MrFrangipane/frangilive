from importlib.resources import files

from PySide6.QtCore import Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy

from pyside6helpers.layout import clear

from frangilive import resources
from frangilive.device.device_library import DeviceLibrary


def _make_button(text: str, checkable=True, color=None):
    button = QPushButton(text)

    stylesheet = "QPushButton:enabled {font-size: 12pt; font-weight: bold;"
    if color is not None:
        stylesheet += f"background-color: {color};"
    stylesheet += "}"
    button.setStyleSheet(stylesheet)

    button.setMinimumWidth(120)
    button.setCheckable(checkable)
    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return button


class CablesWidget(QWidget):
    def __init__(self, left_device_count: int, right_device_count: int, parent=None):
        super().__init__(parent)
        self._connections: list[tuple[int, int]] = []
        self._left_device_count = left_device_count
        self._right_device_count = right_device_count

    def set_left_device_count(self, device_count: int):
        self._left_device_count = device_count
        self.update()

    def set_right_device_count(self, device_count: int):
        self._right_device_count = device_count
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = event.rect().adjusted(1, 1, -1, -1)

        left_height = rect.height() / self._left_device_count
        left_half_height = left_height / 2

        right_height = rect.height() / self._right_device_count
        right_half_height = right_height / 2

        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)

        for left in range(self._left_device_count):
            for right in range(self._right_device_count):
                painter.drawLine(
                    0, int(left_height * left + left_half_height),
                    rect.width(), int(right_height * right + right_half_height),
                )

        painter.end()


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
            button = _make_button(port_name)
            button.clicked.connect(self._emit_changed)
            self._buttons.append(button)
            layout.addWidget(button, row, 0)

        self._emit_changed()

    def _emit_changed(self):
        self.changed.emit([button.text() for button in self._buttons if button.isChecked()])


class Patcher(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._out_buttons: dict[str, QPushButton] = {}
        self._out_selected_instrument: str | None = None
        self._out_selected_ports: list[str] = []

        self._in_buttons: dict[str, QPushButton] = {}
        self._in_selected_instrument: str | None = None
        self._in_selected_ports: list[str] = []

        # FIXME create a DeviceLibraryStore class
        filepath = files(resources).joinpath("devices.json")
        self._device_library: DeviceLibrary = DeviceLibrary.from_json(open(filepath).read())
        self._instrument_count = len(self._device_library.audio_instruments)

        layout = QGridLayout(self)

        # Instruments outputs
        for row, audio_instrument in enumerate(self._device_library.audio_instruments):
            if audio_instrument.outputs:
                out_button = _make_button(audio_instrument.name)
                out_button.clicked.connect(lambda checked, instrument_name=audio_instrument.name: self._out_clicked(instrument_name))
                self._out_buttons[audio_instrument.name] = out_button
                layout.addWidget(out_button, row, 0)

        self._out_ports_widget = PortsWidget()
        self._out_ports_widget.changed.connect(self._out_ports_changed)
        layout.addWidget(self._out_ports_widget, 0, 1, self._instrument_count, 1)

        self._cables_widget = CablesWidget(left_device_count=self._instrument_count, right_device_count=self._instrument_count)
        self._cables_widget._connections = [(i, i) for i in range(self._instrument_count)]
        layout.addWidget(self._cables_widget, 0, 2, self._instrument_count, 2)

        self._in_ports_widget = PortsWidget()
        self._in_ports_widget.changed.connect(self._in_ports_changed)
        layout.addWidget(self._in_ports_widget, 0, 4, self._instrument_count, 1)

        for row, audio_instrument in enumerate(self._device_library.audio_instruments):
            if audio_instrument.inputs:
                in_button = _make_button(audio_instrument.name)
                in_button.clicked.connect(lambda checked, instrument_name=audio_instrument.name: self._in_clicked(instrument_name))
                self._in_buttons[audio_instrument.name] = in_button
                layout.addWidget(in_button, row, 5)

        self.button_disconnect = _make_button("Disconnect", checkable=False, color="#DE3838")
        self.button_disconnect.setEnabled(False)
        layout.addWidget(self.button_disconnect, self._instrument_count, 0, 1, 3)

        self.button_connect = _make_button("Connect", checkable=False, color="#38DE7A")
        self.button_connect.setEnabled(False)
        layout.addWidget(self.button_connect, self._instrument_count, 3, 1, 3)

        layout.setColumnStretch(2, 50)
        layout.setColumnStretch(3, 50)

    def _out_clicked(self, instrument_name: str):
        if self._out_buttons[instrument_name].isChecked():
            self._out_selected_instrument = instrument_name
            for name, button in self._out_buttons.items():
                if name != instrument_name:
                    button.setChecked(False)

            output_names = [output.name for output in self._device_library.audio_instrument(instrument_name).outputs]
            self._cables_widget.set_left_device_count(len(output_names))
            self._out_ports_widget.set_port_names(output_names)

        else:
            self._out_selected_instrument = None
            self._cables_widget.set_left_device_count(self._instrument_count)
            self._out_ports_widget.set_port_names([])

        self._update_action_buttons()

    def _in_clicked(self, instrument_name: str):
        if self._in_buttons[instrument_name].isChecked():
            self._in_selected_instrument = instrument_name
            for name, button in self._in_buttons.items():
                if name != instrument_name:
                    button.setChecked(False)

            input_names = [input_.name for input_ in self._device_library.audio_instrument(instrument_name).inputs]
            self._cables_widget.set_right_device_count(len(input_names))
            self._in_ports_widget.set_port_names(input_names)

        else:
            self._in_selected_instrument = None
            self._cables_widget.set_right_device_count(self._instrument_count)
            self._in_ports_widget.set_port_names([])

        self._update_action_buttons()

    def _out_ports_changed(self, port_names: list[str]):
        self._out_selected_ports = port_names
        self._update_action_buttons()

    def _in_ports_changed(self, port_names: list[str]):
        self._in_selected_ports = port_names
        self._update_action_buttons()

    def _update_action_buttons(self):
        print(self._out_selected_instrument, self._in_selected_instrument, self._out_selected_ports, self._in_selected_ports)

        if self._out_selected_instrument is None or self._in_selected_instrument is None:
            self.button_connect.setEnabled(False)
            self.button_disconnect.setEnabled(False)
            return

        if not self._out_selected_ports or not self._in_selected_ports:
            self.button_connect.setEnabled(False)
            self.button_disconnect.setEnabled(False)
            return

        if self._out_selected_instrument == self._in_selected_instrument:
            self.button_connect.setEnabled(False)
            self.button_disconnect.setEnabled(False)
            return

        self.button_connect.setEnabled(True)
        self.button_disconnect.setEnabled(True)
