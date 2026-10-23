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
_APLAY_CARD_RE = re.compile(r"^card\s+(\d+):\s+([^\s]+)\s+\[([^\]]+)\]", re.MULTILINE)


class JackAudioSystem(AudioRouterGateway, AudioEngineGateway):
    def __init__(self):
        self._jack_client: jack.Client | None = None if jack else None
        self._hardware_name: str | None = None
        self._jack_control_command = ["jack_control"]

    def _detect_hardware_name(self, interface_name: str) -> str:
        output = subprocess.check_output(["aplay", "-l"], text=True)

        for card_number, card_id, card_label in _APLAY_CARD_RE.findall(output):
            if (
                    interface_name.lower() in card_id.lower()
                    or interface_name.lower() in card_label.lower()
            ):
                hardware_name = f"hw:{card_number}"
                _logger.info(
                    "Detected audio interface '%s' as %s: %s [%s]",
                    interface_name,
                    hardware_name,
                    card_id,
                    card_label,
                )
                return hardware_name

        raise RuntimeError(
            f"Could not detect audio interface '{interface_name}' in aplay -l output:\n{output}"
        )

    def _run_jack_control(self, *args: str) -> bytes:
        try:
            return subprocess.check_output(
                [*self._jack_control_command, *args],
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            _logger.error(
                "jack_control failed with exit code %s while running: %s\n%s",
                e.returncode,
                " ".join([*self._jack_control_command, *args]),
                e.output.decode(errors="replace"),
            )
            raise

    def start(self, interface_name: str = "Fireface", buffer_size: int = 128, driver: str = "alsa", connection_type: str = "USB") -> None:
        if jack is None:
            raise ImportError("jack-client package is required for JackAudioRouter")

        _logger.info(f"Detecting audio interface '{interface_name}'...")
        self._hardware_name = self._detect_hardware_name(interface_name)

        # Start server
        _logger.info("Starting JACK server...")
        periods_per_buffer = 2 if connection_type == "PCI" else 3
        try:
            self._run_jack_control("stop")
            self._run_jack_control("ds", driver)
            self._run_jack_control("dps", "device", self._hardware_name)
            self._run_jack_control("dps", "period", str(buffer_size))
            self._run_jack_control("dps", "nperiods", str(periods_per_buffer))
            self._run_jack_control("dps", "rate", "48000")
            self._run_jack_control("start")
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
            self._run_jack_control("stop")
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
