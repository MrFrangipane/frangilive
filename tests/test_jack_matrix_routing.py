import io
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from frangilive.audio.infrastructure.jack_audio_system import JackAudioSystem
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.domain.audio_port import AudioPort
from frangilive.devices.domain.device_library import DeviceLibrary
from frangilive.patcher.application.manage_connections import ManageConnectionsUseCase
from frangilive.patcher.domain.audio_connection import AudioConnection
from frangilive.patcher.domain.patcher import Patcher


class MatrixRoutingTest(unittest.TestCase):
    def setUp(self):
        self.system = JackAudioSystem()
        self.system.configure_ports(DeviceLibrary("test", [AudioInstrument(
            "device", inputs=[AudioPort("input", "sink:1", "sink:2")],
            outputs=[AudioPort("output", "source:1", "source:2")],
        )]))
        self.process = SimpleNamespace(stdin=io.StringIO(), stdout=io.StringIO("OK\n" * 20))

    def test_routes_are_queued_and_reference_counted(self):
        self.system.connect("source:1", "sink:1")
        self.system.connect("source:1", "sink:1")
        self.system._matrix = self.process
        self.system.disconnect("source:1", "sink:1")
        self.assertEqual(self.process.stdin.getvalue(), "")
        self.system.disconnect("source:1", "sink:1")
        self.system.connect("source:2", "sink:2")
        self.assertEqual(self.process.stdin.getvalue(), "SET 0 0 0\nSET 1 1 1\n")

    def test_cue_transition_sends_one_complete_matrix(self):
        source = AudioInstrument("source", outputs=[AudioPort("out", "source:1", "source:2")])
        target = AudioInstrument("target", inputs=[AudioPort("in", "sink:1", "sink:2")])
        patcher = Patcher(DeviceLibrary("test", [source, target]))
        use_case = ManageConnectionsUseCase(self.system, patcher)
        connection = AudioConnection(source, source.outputs[0], target, target.inputs[0])
        self.system._matrix = self.process
        use_case.apply_connections([connection])
        self.assertEqual(self.process.stdin.getvalue(), "MATRIX 0,0 1,1\n")
        self.process.stdin.seek(0)
        self.process.stdin.truncate()
        use_case.apply_connections([])
        self.assertEqual(self.process.stdin.getvalue(), "MATRIX\n")

    def test_cue_replacement_is_one_command_and_failure_keeps_patch(self):
        source = AudioInstrument("source", outputs=[AudioPort("first", "source:1"),
                                                    AudioPort("second", "source:2")])
        target = AudioInstrument("target", inputs=[AudioPort("in", "sink:1")])
        patcher = Patcher(DeviceLibrary("test", [source, target]))
        use_case = ManageConnectionsUseCase(self.system, patcher)
        first = AudioConnection(source, source.outputs[0], target, target.inputs[0])
        second = AudioConnection(source, source.outputs[1], target, target.inputs[0])
        use_case.apply_connections([first])
        self.system._matrix = self.process
        self.process.stdout = io.StringIO("ERR invalid command\nOK\n")
        with self.assertRaises(RuntimeError):
            use_case.apply_connections([second])
        self.assertEqual(patcher.connections, [first])
        use_case.apply_connections([second])
        self.assertEqual(self.process.stdin.getvalue(), "MATRIX 1,0\nMATRIX 1,0\n")
        self.assertEqual(patcher.connections, [second])

    def test_clear_only_disables_matrix_routes(self):
        self.system._matrix = self.process
        self.system.connect("source:1", "sink:1")
        self.system.connect("source:2", "sink:1")
        self.system.remove_all_connections()
        self.assertEqual(self.process.stdin.getvalue(),
                         "SET 0 0 1\nSET 1 0 1\nMATRIX\n")
        self.assertFalse(self.system._routes)

    def test_bulk_update_preserves_counts_and_failure_leaves_state_unchanged(self):
        route = ("source:1", "sink:1")
        self.system.set_connections([route, route])
        self.system._matrix = self.process
        self.process.stdout = io.StringIO("ERR invalid command\n")
        with self.assertRaises(RuntimeError):
            self.system.set_connections([("source:2", "sink:2")])
        self.assertEqual(self.system._routes, {route: 2})
        self.process.stdout = io.StringIO("OK\n")
        self.system.disconnect(*route)
        self.assertEqual(self.system._routes, {route: 1})

    def test_failure_does_not_change_route_state(self):
        self.process.stdout = io.StringIO("ERR invalid command\n")
        self.system._matrix = self.process
        with self.assertRaises(RuntimeError):
            self.system.connect("source:1", "sink:1")
        self.assertFalse(self.system._routes)

    def test_device_wiring_is_independent_of_routes(self):
        client = Mock()
        client.get_all_connections.return_value = []
        self.system._jack_client = client
        with patch("frangilive.audio.infrastructure.jack_audio_system.jack", SimpleNamespace(JackError=Exception)):
            self.system._wire_ports()
        self.assertEqual(client.connect.call_count, 4)
        client.connect.assert_any_call("source:1", "jack-matrix:in_0")
        client.connect.assert_any_call("jack-matrix:out_1", "sink:2")
        self.assertFalse(self.system._routes)

    def test_wiring_verifies_every_connection_and_retries_missing_ones(self):
        connections = set()
        unavailable = {"source:2", "sink:2"}
        client = Mock()
        client.get_port_by_name.side_effect = lambda name: name
        client.get_all_connections.side_effect = lambda port: [
            SimpleNamespace(name=target) for source, target in connections if source == port
        ]

        class JackError(Exception):
            pass

        def connect(source, target):
            if source in unavailable or target in unavailable:
                raise JackError("port unavailable")
            connections.add((source, target))

        client.connect.side_effect = connect
        self.system._jack_client = client
        with patch("frangilive.audio.infrastructure.jack_audio_system.jack", SimpleNamespace(JackError=JackError)):
            with self.assertLogs("frangilive.audio.infrastructure.jack_audio_system", level="WARNING") as logs:
                self.system._wire_ports()
            self.assertIn("source:2", " ".join(logs.output))
            self.assertIn("sink:2", " ".join(logs.output))
            self.assertEqual(len(connections), 2)
            unavailable.clear()
            self.system._wire_ports()
            self.assertEqual(len(connections), 4)
            connections.remove(("source:1", "jack-matrix:in_0"))
            self.system._wire_ports()
            self.assertEqual(len(connections), 4)

    def test_wiring_reports_connection_not_observed_after_connect(self):
        client = Mock()
        client.get_all_connections.return_value = []
        self.system._jack_client = client
        with patch("frangilive.audio.infrastructure.jack_audio_system.jack", SimpleNamespace(JackError=Exception)):
            with self.assertLogs("frangilive.audio.infrastructure.jack_audio_system", level="WARNING") as logs:
                self.system._wire_ports()
        self.assertIn("source:1", " ".join(logs.output))
        self.assertIn("sink:1", " ".join(logs.output))

    def test_start_replays_queued_routes_and_stop_closes_process(self):
        self.system.connect("source:2", "sink:1")
        client = Mock()
        client.get_all_connections.return_value = []
        self.process.wait = Mock()
        self.process.poll = Mock(return_value=None)
        fake_jack = SimpleNamespace(Client=Mock(return_value=client), JackError=Exception)
        with patch("frangilive.audio.infrastructure.jack_audio_system.jack", fake_jack), \
             patch("frangilive.audio.infrastructure.jack_audio_system.subprocess.Popen", return_value=self.process), \
             patch("frangilive.audio.infrastructure.jack_audio_system.subprocess.check_output"), \
             patch("frangilive.audio.infrastructure.jack_audio_system.time.sleep"), \
             patch.object(self.system, "_detect_hardware_name", return_value="hw:1"), \
             patch.object(self.system, "_run_jack_control"):
            self.system.start()
            self.assertTrue(self.system.is_running())
            self.assertEqual(self.process.stdin.getvalue(), "SET 0 0 0\nMATRIX 1,0\n")
            self.system.stop()
        client.close.assert_called_once()
        self.process.wait.assert_called_once()
        self.assertFalse(self.system.is_running())


if __name__ == "__main__":
    unittest.main()