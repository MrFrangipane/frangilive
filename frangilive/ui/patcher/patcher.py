from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton

from frangilive.patcher.audio_connection_info import AudioConnectionInfo
from frangilive.patcher.patcher import Patcher
from frangilive.ui.patcher.cables import CablesWidget
from frangilive.ui.patcher.make_button import make_button
from frangilive.ui.patcher.ports import PortsWidget


class PatcherWidget(QWidget):

    connected = Signal(AudioConnectionInfo)
    disconnected = Signal(AudioConnectionInfo)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._patcher = Patcher()

        self._out_buttons: dict[str, QPushButton] = {}
        self._out_selected_instrument: str | None = None
        self._out_selected_ports: list[str] = []

        self._in_buttons: dict[str, QPushButton] = {}
        self._in_selected_instrument: str | None = None
        self._in_selected_ports: list[str] = []

        layout = QGridLayout(self)

        # Instruments outputs
        for row, audio_instrument in enumerate(self._patcher.all_instruments()):
            if audio_instrument.outputs:
                out_button = make_button(audio_instrument.name)
                out_button.clicked.connect(lambda checked, instrument_name=audio_instrument.name: self._out_clicked(instrument_name))
                self._out_buttons[audio_instrument.name] = out_button
                layout.addWidget(out_button, row, 0)

        # Instruments out ports
        self._out_ports_widget = PortsWidget()
        self._out_ports_widget.changed.connect(self._out_ports_changed)
        layout.addWidget(self._out_ports_widget, 0, 1, self._patcher.instrument_count(), 1)

        # Cables
        self._cables_widget = CablesWidget(left_device_count=self._patcher.instrument_count(), right_device_count=self._patcher.instrument_count())
        layout.addWidget(self._cables_widget, 0, 2, self._patcher.instrument_count(), 2)

        # Instruments in ports
        self._in_ports_widget = PortsWidget()
        self._in_ports_widget.changed.connect(self._in_ports_changed)
        layout.addWidget(self._in_ports_widget, 0, 4, self._patcher.instrument_count(), 1)

        # Instruments inputs
        for row, audio_instrument in enumerate(self._patcher.all_instruments()):
            if audio_instrument.inputs:
                in_button = make_button(audio_instrument.name)
                in_button.clicked.connect(lambda checked, instrument_name=audio_instrument.name: self._in_clicked(instrument_name))
                self._in_buttons[audio_instrument.name] = in_button
                layout.addWidget(in_button, row, 5)

        # Actions
        self.button_disconnect = make_button("Disconnect", checkable=False, color="#DE3838")
        self.button_disconnect.setEnabled(False)
        self.button_disconnect.clicked.connect(self._disconnect)
        layout.addWidget(self.button_disconnect, self._patcher.instrument_count(), 0, 1, 3)

        self.button_connect = make_button("Connect", checkable=False, color="#38DE7A")
        self.button_connect.setEnabled(False)
        self.button_connect.clicked.connect(self._connect)
        layout.addWidget(self.button_connect, self._patcher.instrument_count(), 3, 1, 3)

        layout.setColumnStretch(2, 50)
        layout.setColumnStretch(3, 50)

    def _out_clicked(self, instrument_name: str):
        if self._out_buttons[instrument_name].isChecked():
            self._out_selected_instrument = instrument_name
            for name, button in self._out_buttons.items():
                if name != instrument_name:
                    button.setChecked(False)

            output_names = [output.name for output in self._patcher.audio_instrument(instrument_name).outputs]
            self._out_ports_widget.set_port_names(output_names)

        else:
            self._out_selected_instrument = None
            self._out_ports_widget.set_port_names([])

        self._update_cables()
        self._update_action_buttons()

    def _in_clicked(self, instrument_name: str):
        if self._in_buttons[instrument_name].isChecked():
            self._in_selected_instrument = instrument_name
            for name, button in self._in_buttons.items():
                if name != instrument_name:
                    button.setChecked(False)

            input_names = [input_.name for input_ in self._patcher.audio_instrument(instrument_name).inputs]
            self._in_ports_widget.set_port_names(input_names)

        else:
            self._in_selected_instrument = None
            self._in_ports_widget.set_port_names([])

        self._update_cables()
        self._update_action_buttons()

    def _out_ports_changed(self, port_names: list[str]):
        self._out_selected_ports = port_names
        self._update_action_buttons()

    def _in_ports_changed(self, port_names: list[str]):
        self._in_selected_ports = port_names
        self._update_action_buttons()

    def _update_action_buttons(self):
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

    def _connect(self):
        for port_out_name in self._out_selected_ports:
            for port_in_name in self._in_selected_ports:
                connection_info = AudioConnectionInfo(
                    source_instrument=self._out_selected_instrument,
                    source_port=port_out_name,
                    target_instrument=self._in_selected_instrument,
                    target_port=port_in_name
                )
                if self._patcher.connect(connection_info):
                    self.connected.emit(connection_info)

        self._update_cables()

    def _disconnect(self):
        for port_out_name in self._out_selected_ports:
            for port_in_name in self._in_selected_ports:
                connection_info = AudioConnectionInfo(
                        source_instrument=self._out_selected_instrument,
                        source_port=port_out_name,
                        target_instrument=self._in_selected_instrument,
                        target_port=port_in_name
                    )
                if self._patcher.disconnect(connection_info):
                    self.disconnected.emit(connection_info)

        self._update_cables()

    def _update_cables(self):
        self._cables_widget.clear_connections()

        if self._out_selected_instrument is None:
            self._cables_widget.set_left_device_count(len(self._patcher._instruments_with_output))
        else:
            self._cables_widget.set_left_device_count(len(self._patcher.audio_instrument(self._out_selected_instrument).outputs))

        if self._in_selected_instrument is None:
            self._cables_widget.set_right_device_count(len(self._patcher._instruments_with_input))
        else:
            self._cables_widget.set_right_device_count(len(self._patcher.audio_instrument(self._in_selected_instrument).inputs))

        if self._out_selected_instrument is not None and self._in_selected_instrument is not None:
            source = self._patcher.audio_instrument(self._out_selected_instrument)
            target = self._patcher.audio_instrument(self._in_selected_instrument)
            connections = self._patcher.connections_between_instruments(source, target)
            for connection in connections:
                left_index = self._patcher.audio_instrument(self._out_selected_instrument).outputs.index(connection.source_port)
                right_index = self._patcher.audio_instrument(self._in_selected_instrument).inputs.index(connection.target_port)
                self._cables_widget.add_connection(left_index, right_index)

        self._cables_widget.update()
