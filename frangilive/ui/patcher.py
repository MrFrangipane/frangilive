from importlib.resources import files

from PySide6.QtCore import Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy

from pyside6helpers.layout import clear

from frangilive import resources
from frangilive.device.device_library import DeviceLibrary


def _make_button(text: str, parent=None):
    button = QPushButton(text)
    button.setStyleSheet("font-size: 12pt; font-weight: bold;")
    button.setMinimumWidth(120)
    button.setCheckable(True)
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

    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(QGridLayout())

    def set_port_names(self, port_names: list[str]):
        self.setVisible(len(port_names) > 0)

        layout: QGridLayout = self.layout()
        clear(layout)

        for row, port_name in enumerate(port_names):
            button = _make_button(port_name)
            button.clicked.connect(lambda checked, port_name=port_name: self.clicked.emit(port_name))
            layout.addWidget(button, row, 0)


class Patcher(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._in_buttons: dict[str, QPushButton] = {}
        self._out_buttons: dict[str, QPushButton] = {}

        filepath = files(resources).joinpath("devices.json")
        self._device_library: DeviceLibrary = DeviceLibrary.from_json(open(filepath).read())
        self._instrument_count = len(self._device_library.audio_instruments)

        layout = QGridLayout(self)

        for row, audio_instrument in enumerate(self._device_library.audio_instruments):
            if audio_instrument.outputs:
                out_button = _make_button(audio_instrument.name)
                out_button.clicked.connect(lambda checked, instrument_name=audio_instrument.name: self._out_clicked(instrument_name))
                self._out_buttons[audio_instrument.name] = out_button
                layout.addWidget(out_button, row, 0)

            if audio_instrument.inputs:
                in_button = _make_button(audio_instrument.name)
                in_button.clicked.connect(lambda checked, instrument_name=audio_instrument.name: self._in_clicked(instrument_name))
                self._in_buttons[audio_instrument.name] = in_button
                layout.addWidget(in_button, row, 4)

        self._cables_widget = CablesWidget(left_device_count=self._instrument_count, right_device_count=self._instrument_count)
        self._cables_widget._connections = [(i, i) for i in range(self._instrument_count)]
        layout.addWidget(self._cables_widget, 0, 2, len(self._device_library.audio_instruments), 1)

        self.out_ports_widget = PortsWidget()
        layout.addWidget(self.out_ports_widget, 0, 1, len(self._device_library.audio_instruments), 1)

        self.in_ports_widget = PortsWidget()
        layout.addWidget(self.in_ports_widget, 0, 3, len(self._device_library.audio_instruments), 1)

        layout.setColumnStretch(2, 100)

    def _out_clicked(self, instrument_name: str):
        if self._out_buttons[instrument_name].isChecked():
            for name, button in self._out_buttons.items():
                if name != instrument_name:
                    button.setChecked(False)

            output_names = [output.name for output in self._device_library.audio_instrument(instrument_name).outputs]
            self._cables_widget.set_left_device_count(len(output_names))
            self.out_ports_widget.set_port_names(output_names)
        else:
            self._cables_widget.set_left_device_count(self._instrument_count)
            self.out_ports_widget.set_port_names([])

    def _in_clicked(self, instrument_name: str):
        if self._in_buttons[instrument_name].isChecked():
            for name, button in self._in_buttons.items():
                if name != instrument_name:
                    button.setChecked(False)

            input_names = [input_.name for input_ in self._device_library.audio_instrument(instrument_name).inputs]
            self._cables_widget.set_right_device_count(len(input_names))
            self.in_ports_widget.set_port_names(input_names)

        else:
            self._cables_widget.set_right_device_count(self._instrument_count)
            self.in_ports_widget.set_port_names([])
