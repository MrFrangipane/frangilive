import logging
import re
import subprocess
import time

import jack

from frangilive.audio.audio_interface import AudioInterface
from frangilive.audio.interface_connection_type import InterfaceConnectionType
from frangilive.audio.jack_options import JackOptions
from frangilive.audio.port import AudioPort
from frangilive.audio.router.abstract import AbstractAudioRouter


_logger = logging.getLogger(__name__)
_RE = re.compile(r'card ([0-9]+)[^\[]+\[([^\]]+)')


class RaspberryPiAudioRouter(AbstractAudioRouter):

    def __init__(self):
        self._jack_client: jack.Client | None = None
        self._audio_interface: AudioInterface | None = None

    def find_audio_interface(self, name: str) -> bool:
        _logger.info(f"Detecting audio interface '{name}'...")

        output = subprocess.check_output(["aplay", "-l"]).decode()

        for result in _RE.findall(output):
            number_listed, name_listed = result
            if name.lower() in name_listed.lower():
                detected_interface = AudioInterface(
                    name=name_listed,
                    hardware_name=f"hw:{number_listed}"
                )
                _logger.info(f"Detected interface: {detected_interface}")
                self._audio_interface = detected_interface
                return True

        _logger.info(f"Could not detect '{name}' with aplay -l")
        return False

    def start_jack_server(self, options: JackOptions):
        _logger.info("Starting JACK server...")

        periods_per_buffer = 2 if options.interface_connection_type == InterfaceConnectionType.PCI else 3

        subprocess.check_output(["jack_control", "ds", options.driver.value])
        subprocess.check_output(["jack_control", "dps", "device", self._audio_interface.hardware_name])
        subprocess.check_output(["jack_control", "dps", "period", str(options.buffer_size)])
        subprocess.check_output(["jack_control", "dps", "nperiods", str(periods_per_buffer)])
        subprocess.check_output(["jack_control", "start"])

        _logger.info("JACK server started")

    def start_overwitch(self):
        _logger.info("Starting Overwitch...")
        subprocess.check_output(["systemctl", "--user", "restart", "overwitch"])
        time.sleep(1)  # FIXME
        # print(subprocess.check_output(["systemctl", "--user", "status", "overwitch"]).decode())
        _logger.info("Overwitch started")

    def activate_jack_client(self):
        if self._jack_client is not None:
            raise RuntimeError("Jack client already active")

        self._jack_client = jack.Client("Frangilive")
        self._jack_client.activate()

        # print("JACK audio ports")
        # pp(client.get_ports(is_audio=True))

        # print("JACK MIDI ports")
        # pp(client.get_ports(is_midi=True))

    def remove_all_audio_connections(self):
        _logger.info("Disconnecting all JACK connections...")
        def disconnect_all(port_name):
            port = self._jack_client.get_port_by_name(port_name)
            for connected_port in self._jack_client.get_all_connections(port):
                try:
                    if port.is_output:
                        self._jack_client.disconnect(port_name, connected_port.name)
                    else:
                        self._jack_client.disconnect(connected_port.name, port_name)
                except jack.JackError:
                    pass

        for port in self._jack_client.get_ports():
            disconnect_all(port.name)

    def connect(self, input_info: tuple[str, AudioPort], output_info: tuple[str, AudioPort]) -> None:
        # TODO check input/output order and fix it if necessary ? Or catch and re raise Jack error ?
        input_instrument_name, input_port = input_info
        output_instrument_name, output_port = output_info

        _logger.info(f"Connecting {input_instrument_name}.{input_port.name} -> {output_instrument_name}.{output_port.name} ({input_port.left} -> {output_port.left})")

        if input_port.is_stereo:
            if output_port.is_stereo:
                self._jack_client.connect(input_port.left, output_port.left)
                self._jack_client.connect(input_port.right, output_port.right)
            else:
                self._jack_client.connect(input_port.left, output_port.left)
                self._jack_client.connect(input_port.right, output_port.left)
        else:
            if output_port.is_stereo:
                self._jack_client.connect(input_port.left, output_port.left)
                self._jack_client.connect(input_port.left, output_port.right)
            else:
                self._jack_client.connect(input_port.left, output_port.left)
