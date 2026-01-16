import logging
import re
import subprocess
import time

try:
    import jack
except ImportError:
    jack = None

from frangilive.audio.interfaces.audio_router import AudioRouterGateway
from frangilive.audio.interfaces.audio_engine import AudioEngineGateway

_logger = logging.getLogger(__name__)
_RE = re.compile(r'card ([0-9]+)[^\[]+\[([^\]]+)')


class JackAudioSystem(AudioRouterGateway, AudioEngineGateway):
    def __init__(self):
        self._jack_client: jack.Client | None = None if jack else None
        self._hardware_name: str | None = None

    def start(self, interface_name: str = "Fireface", buffer_size: int = 128, driver: str = "alsa", connection_type: str = "USB") -> None:
        if jack is None:
            raise ImportError("jack-client package is required for JackAudioRouter")

        # Find the hardware name
        _logger.info(f"Detecting audio interface '{interface_name}'...")
        try:
            output = subprocess.check_output(["aplay", "-l"]).decode()
            for result in _RE.findall(output):
                number_listed, name_listed = result
                if interface_name.lower() in name_listed.lower():
                    self._hardware_name = f"hw:{number_listed}"
                    break
        except Exception as e:
            _logger.warning(f"Failed to run aplay: {e}")

        if not self._hardware_name:
            _logger.warning(f"Could not detect '{interface_name}' hardware name, using default 'hw:0'")
            self._hardware_name = "hw:0"

        # Start server
        _logger.info("Starting JACK server...")
        periods_per_buffer = 2 if connection_type == "PCI" else 3
        try:
            subprocess.check_output(["jack_control", "ds", driver])
            subprocess.check_output(["jack_control", "dps", "device", self._hardware_name])
            subprocess.check_output(["jack_control", "dps", "period", str(buffer_size)])
            subprocess.check_output(["jack_control", "dps", "nperiods", str(periods_per_buffer)])
            subprocess.check_output(["jack_control", "start"])
        except Exception as e:
            _logger.error(f"Failed to start JACK server via jack_control: {e}")
            raise

        # Overwitch
        _logger.info("Starting Overwitch...")
        try:
            subprocess.check_output(["systemctl", "--user", "restart", "overwitch"])
            time.sleep(1)
        except Exception as e:
            _logger.warning(f"Failed to start overwitch: {e}")

        # Activate client
        self._jack_client = jack.Client("Frangilive")
        self._jack_client.activate()
        _logger.info("JACK client activated")

    def stop(self) -> None:
        if self._jack_client:
            self._jack_client.close()
            self._jack_client = None
        try:
            subprocess.check_output(["jack_control", "stop"])
        except Exception as e:
            _logger.warning(f"Failed to stop JACK server: {e}")

    def is_running(self) -> bool:
        return self._jack_client is not None

    def connect(self, source_port_name: str, target_port_name: str) -> None:
        if not self._jack_client:
            raise RuntimeError("JACK client not active")
        _logger.info(f"Connecting {source_port_name} to {target_port_name}")
        try:
            self._jack_client.connect(source_port_name, target_port_name)
        except jack.JackError as e:
            _logger.warning(f"Failed to connect ports: {e}")

    def disconnect(self, source_port_name: str, target_port_name: str) -> None:
        if not self._jack_client:
            raise RuntimeError("JACK client not active")
        _logger.info(f"Disconnecting {source_port_name} from {target_port_name}")
        try:
            self._jack_client.disconnect(source_port_name, target_port_name)
        except jack.JackError as e:
            _logger.warning(f"Failed to disconnect ports: {e}")

    def remove_all_connections(self) -> None:
        if not self._jack_client:
            raise RuntimeError("JACK client not active")
        _logger.info("Removing all JACK connections")
        for port in self._jack_client.get_ports():
            self._disconnect_all(port.name)

    def _disconnect_all(self, port_name):
        port = self._jack_client.get_port_by_name(port_name)
        for connected_port in self._jack_client.get_all_connections(port):
            try:
                if port.is_output:
                    self._jack_client.disconnect(port_name, connected_port.name)
                else:
                    self._jack_client.disconnect(connected_port.name, port_name)
            except jack.JackError:
                pass
