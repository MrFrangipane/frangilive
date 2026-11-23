import logging
import re
import subprocess
import threading
import time
from pathlib import Path

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
        self._sources = {}
        self._targets = {}
        self._routes = {}
        self._matrix = None
        self._wire_stop = threading.Event()
        self._wire_thread = None

    def configure_ports(self, device_library) -> None:
        if self._matrix is not None:
            raise RuntimeError("Cannot reconfigure a running matrix")
        sources, targets = {}, {}
        for instrument in device_library.audio_instruments:
            for ports, mapping in ((instrument.outputs, sources), (instrument.inputs, targets)):
                for port in ports:
                    for name in (port.left, port.right):
                        if name and name not in mapping:
                            mapping[name] = len(mapping)
        if len(sources) > 128 or len(targets) > 128:
            raise ValueError("JACK matrix supports at most 128 input and output channels")
        self._sources, self._targets = sources, targets

    def _set_route(self, source, target, enabled):
        self._matrix.stdin.write(f"SET {self._sources[source]} {self._targets[target]} {int(enabled)}\n")
        self._matrix.stdin.flush()
        response = self._matrix.stdout.readline().strip()
        if response != "OK":
            raise RuntimeError(f"JACK matrix command failed: {response or 'process exited'}")

    def _wire_ports(self):
        for source, index in self._sources.items():
            self._ensure_wire(source, f"jack-matrix:in_{index}")
        for target, index in self._targets.items():
            self._ensure_wire(f"jack-matrix:out_{index}", target)

    def _ensure_wire(self, source, target):
        try:
            port = self._jack_client.get_port_by_name(source)
            if target not in {p.name for p in self._jack_client.get_all_connections(port)}:
                self._jack_client.connect(source, target)
        except jack.JackError:
            # Devices may appear after JACK starts; the worker retries their wiring.
            pass

    def _wire_loop(self):
        while not self._wire_stop.wait(1):
            self._wire_ports()

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
        try:
            binary = Path(__file__).resolve().parents[3] / "native" / "jack-matrix"
            self._matrix = subprocess.Popen(
                [str(binary), "--inputs", str(max(1, len(self._sources))),
                 "--outputs", str(max(1, len(self._targets)))],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
            )
            # The first response confirms that the process registered its JACK ports.
            self._matrix.stdin.write("SET 0 0 0\n")
            self._matrix.stdin.flush()
            if self._matrix.stdout.readline().strip() != "OK":
                raise RuntimeError("JACK matrix failed to start")
            self._wire_ports()
            for source, target in self._routes:
                self._set_route(source, target, True)
            self._wire_stop.clear()
            self._wire_thread = threading.Thread(target=self._wire_loop, daemon=True)
            self._wire_thread.start()
        except Exception:
            self.stop()
            raise
        _logger.info("JACK client activated")

    def stop(self) -> None:
        self._wire_stop.set()
        if self._wire_thread:
            self._wire_thread.join()
            self._wire_thread = None
        if self._matrix:
            self._matrix.stdin.close()
            try:
                self._matrix.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._matrix.kill()
                self._matrix.wait()
            self._matrix.stdout.close()
            self._matrix = None
        if self._jack_client:
            self._jack_client.close()
            self._jack_client = None
        try:
            self._run_jack_control("stop")
        except Exception as e:
            _logger.warning(f"Failed to stop JACK server: {e}")

    def is_running(self) -> bool:
        return self._jack_client is not None and self._matrix is not None and self._matrix.poll() is None

    def connect(self, source_port_name: str, target_port_name: str) -> None:
        if source_port_name not in self._sources or target_port_name not in self._targets:
            raise ValueError("Unknown matrix source or target port")
        route = (source_port_name, target_port_name)
        count = self._routes.get(route, 0)
        if not count and self._matrix:
            self._set_route(*route, True)
        self._routes[route] = count + 1

    def disconnect(self, source_port_name: str, target_port_name: str) -> None:
        route = (source_port_name, target_port_name)
        count = self._routes.get(route, 0)
        if count == 1:
            if self._matrix:
                self._set_route(*route, False)
            del self._routes[route]
        elif count > 1:
            self._routes[route] = count - 1

    def remove_all_connections(self) -> None:
        for source, target in list(self._routes):
            if self._matrix:
                self._set_route(source, target, False)
            del self._routes[(source, target)]
