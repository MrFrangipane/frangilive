import unittest
from frangilive.app import FrangiliveApp
from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.domain.audio_port import AudioPort
from frangilive.devices.domain.device_library import DeviceLibrary
from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository
from frangilive.midi.infrastructure.mido_midi_gateway import MidoMidiGateway
from frangilive.patcher.domain.audio_connection import AudioConnection, AudioConnectionSnapshot
from frangilive.cues.domain.cue import Cue, CueSnapshot
from frangilive.cues.domain.cue_list import CueList, CueListSnapshot
from frangilive.patcher.domain.patcher import Patcher
from frangilive.patcher.application.manage_connections import ManageConnectionsUseCase
from frangilive.cues.application.manage_cues import ManageCuesUseCase


class TestCueDomainAndApplication(unittest.TestCase):

    def setUp(self):
        self.inst_a = AudioInstrument(
            name="SynthA",
            inputs=[AudioPort(name="In1", left="sys:in1")],
            outputs=[AudioPort(name="Out1", left="sys:out1"), AudioPort(name="Out2", left="sys:out2")],
        )
        self.inst_b = AudioInstrument(
            name="EffectB",
            inputs=[AudioPort(name="In1", left="sys:in2"), AudioPort(name="In2", left="sys:in3")],
            outputs=[AudioPort(name="Out1", left="sys:out3")],
        )
        self.inst_c = AudioInstrument(
            name="MasterC",
            inputs=[AudioPort(name="In1", left="sys:in4")],
            outputs=[],
        )
        self.library = DeviceLibrary(
            name="TestLib",
            audio_instruments=[self.inst_a, self.inst_b, self.inst_c],
        )
        self.patcher = Patcher(device_library=self.library)
        self.mock_audio = MockAudioSystem()
        self.manage_connections = ManageConnectionsUseCase(
            router_gateway=self.mock_audio,
            patcher=self.patcher,
        )
        self.cue_list = CueList()
        self.manage_cues = ManageCuesUseCase(
            cue_list=self.cue_list,
            manage_connections=self.manage_connections,
            patcher=self.patcher,
        )

    def test_cue_dataclass_initialization(self):
        conn = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        cue = Cue(name="Intro", connections=[conn])

        self.assertEqual(cue.name, "Intro")
        self.assertEqual(cue.connection_count(), 1)
        self.assertEqual(cue.connections, [conn])

        # Test setting connections
        conn2 = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])
        cue.set_connections([conn, conn2])
        self.assertEqual(cue.connection_count(), 2)

    def test_cue_list_empty_and_add(self):
        self.assertIsNone(self.cue_list.current_cue)
        self.assertEqual(len(self.cue_list), 0)

        conn1 = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        cue1 = self.cue_list.create_cue_from_connections([conn1], name="Verse")

        self.assertEqual(len(self.cue_list), 1)
        self.assertEqual(self.cue_list.current_index, 0)
        self.assertEqual(self.cue_list.current_cue, cue1)
        self.assertEqual(cue1.name, "Verse")

        # Add second cue with default name
        cue2 = self.cue_list.create_cue_from_connections([])
        self.assertEqual(len(self.cue_list), 2)
        self.assertEqual(self.cue_list.current_index, 1)
        self.assertEqual(self.cue_list.current_cue, cue2)
        self.assertEqual(cue2.name, "Cue 2")

    def test_cue_list_navigation(self):
        conn1 = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn2 = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])

        cue1 = self.cue_list.create_cue_from_connections([conn1], name="Cue 1")
        cue2 = self.cue_list.create_cue_from_connections([conn2], name="Cue 2")
        cue3 = self.cue_list.create_cue_from_connections([conn1, conn2], name="Cue 3")

        # Currently at Cue 3 (index 2)
        self.assertEqual(self.cue_list.current_cue, cue3)

        # Go to first cue
        first = self.cue_list.go_to_first_cue()
        self.assertEqual(first, cue1)
        self.assertEqual(self.cue_list.current_index, 0)

        # Go to next cue
        nxt = self.cue_list.go_to_next_cue()
        self.assertEqual(nxt, cue2)
        self.assertEqual(self.cue_list.current_index, 1)

        # Go to next cue again
        nxt2 = self.cue_list.go_to_next_cue()
        self.assertEqual(nxt2, cue3)
        self.assertEqual(self.cue_list.current_index, 2)

        # Go to next cue at boundary stays at last
        nxt3 = self.cue_list.go_to_next_cue()
        self.assertEqual(nxt3, cue3)
        self.assertEqual(self.cue_list.current_index, 2)

        # Go to previous cue
        prev = self.cue_list.go_to_previous_cue()
        self.assertEqual(prev, cue2)
        self.assertEqual(self.cue_list.current_index, 1)

        # Go to direct cue index
        direct = self.cue_list.go_to_cue(0)
        self.assertEqual(direct, cue1)
        self.assertEqual(self.cue_list.current_index, 0)

    def test_cue_list_save_current_cue(self):
        conn1 = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn2 = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])

        cue1 = self.cue_list.create_cue_from_connections([conn1], name="Cue 1")
        self.assertEqual(cue1.connections, [conn1])

        # Overwrite current cue with conn2
        saved = self.cue_list.save_current_cue([conn2])
        self.assertEqual(saved, cue1)
        self.assertEqual(cue1.connections, [conn2])

    def test_cue_list_removal(self):
        cue1 = self.cue_list.create_cue_from_connections([], name="Cue 1")
        cue2 = self.cue_list.create_cue_from_connections([], name="Cue 2")
        cue3 = self.cue_list.create_cue_from_connections([], name="Cue 3")

        self.cue_list.go_to_cue(1)
        self.assertEqual(self.cue_list.current_index, 1)

        # Remove cue 1 (index 0)
        removed = self.cue_list.remove_cue(0)
        self.assertEqual(removed, cue1)
        self.assertEqual(len(self.cue_list), 2)
        self.assertEqual(self.cue_list.current_index, 0)
        self.assertEqual(self.cue_list.current_cue, cue2)

        # Delete current cue (index 0 -> cue2)
        removed2 = self.cue_list.delete_current_cue()
        self.assertEqual(removed2, cue2)
        self.assertEqual(len(self.cue_list), 1)
        self.assertEqual(self.cue_list.current_index, 0)
        self.assertEqual(self.cue_list.current_cue, cue3)

        # Delete last remaining cue
        removed3 = self.cue_list.delete_current_cue()
        self.assertEqual(removed3, cue3)
        self.assertEqual(len(self.cue_list), 0)
        self.assertIsNone(self.cue_list.current_index)
        self.assertIsNone(self.cue_list.current_cue)

    def test_manage_cues_use_case_flow(self):
        # 1. Connect SynthA -> EffectB
        self.manage_connections.connect("SynthA", "Out1", "EffectB", "In1")
        self.assertEqual(len(self.patcher.connections), 1)

        # 2. Create a new cue from current patch
        cue1 = self.manage_cues.create_cue_from_current_patch(name="Part 1")
        self.assertEqual(cue1.name, "Part 1")
        self.assertEqual(len(cue1.connections), 1)
        self.assertEqual(self.cue_list.current_cue, cue1)

        # 3. Add another connection: EffectB -> MasterC
        self.manage_connections.connect("EffectB", "Out1", "MasterC", "In1")
        self.assertEqual(len(self.patcher.connections), 2)

        # 4. Create second cue
        cue2 = self.manage_cues.create_cue_from_current_patch(name="Part 2")
        self.assertEqual(cue2.name, "Part 2")
        self.assertEqual(len(cue2.connections), 2)

        # 5. Empty patch
        self.manage_cues.empty_patch()
        self.assertEqual(len(self.patcher.connections), 0)

        # 6. Go to first cue
        loaded_cue = self.manage_cues.go_to_first_cue()
        self.assertEqual(loaded_cue, cue1)
        self.assertEqual(len(self.patcher.connections), 1)
        self.assertEqual(self.patcher.connections[0].source_instrument.name, "SynthA")

        # 7. Modify live patch and save to current cue
        self.manage_connections.connect("SynthA", "Out2", "EffectB", "In2")
        self.assertEqual(len(self.patcher.connections), 2)
        self.manage_cues.save_current_patch_to_current_cue()
        self.assertEqual(len(cue1.connections), 2)

        # 8. Go to next cue
        loaded_next = self.manage_cues.go_to_next_cue()
        self.assertEqual(loaded_next, cue2)
        self.assertEqual(len(self.patcher.connections), 2)
        self.assertEqual(self.patcher.connections[1].target_instrument.name, "MasterC")

        # 9. Delete cue 2 (Part 2)
        deleted = self.manage_cues.delete_current_cue()
        self.assertEqual(deleted, cue2)
        self.assertEqual(len(self.cue_list), 1)
        self.assertEqual(self.cue_list.current_cue, cue1)
        # Patch should automatically update to remaining active cue (cue1)
        self.assertEqual(len(self.patcher.connections), 2)
        self.assertEqual(self.patcher.connections[0].source_instrument.name, "SynthA")

        # 10. Delete last remaining cue (cue1)
        deleted_last = self.manage_cues.delete_current_cue()
        self.assertEqual(deleted_last, cue1)
        self.assertEqual(len(self.cue_list), 0)
        self.assertIsNone(self.cue_list.current_cue)
        self.assertEqual(len(self.patcher.connections), 0)

    def test_frangilive_app_cue_methods(self):
        app = FrangiliveApp(
            device_repo=JsonDeviceRepository(),
            audio_router=MockAudioSystem(),
            audio_engine=MockAudioSystem(),
            midi_gateway=MidoMidiGateway(),
            auto_save_cues_on_exit=False,
        )

        digitakt = app.device_library.get_instrument("Digitakt")
        main_lr = app.device_library.get_instrument("Main LR")
        app.connect("Digitakt", digitakt.get_default_output().name, "Main LR", main_lr.get_default_input().name)
        cue1 = app.create_cue_from_current_patch(name="Track 1")
        self.assertEqual(len(app.cue_list), 1)
        self.assertEqual(app.cue_list.current_cue, cue1)

        app.empty_patch()
        self.assertEqual(len(app.patcher.connections), 0)

        app.go_to_first_cue()
        self.assertEqual(len(app.patcher.connections), 1)

        # Delete cue from app
        del_cue = app.delete_current_cue()
        self.assertEqual(del_cue, cue1)
        self.assertEqual(len(app.cue_list), 0)
        self.assertEqual(len(app.patcher.connections), 0)

    def test_audio_connection_snapshot_roundtrip(self):
        conn = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        snapshot = conn.to_snapshot()

        self.assertEqual(snapshot.source_instrument, "SynthA")
        self.assertEqual(snapshot.source_port, "Out1")
        self.assertEqual(snapshot.target_instrument, "EffectB")
        self.assertEqual(snapshot.target_port, "In1")

        # Immutability
        with self.assertRaises(Exception):
            setattr(snapshot, "source_instrument", "Other")

        # Dict serialization / deserialization
        data = snapshot.to_dict()
        self.assertEqual(data, {
            "source_instrument": "SynthA",
            "source_port": "Out1",
            "target_instrument": "EffectB",
            "target_port": "In1",
        })
        rebuilt_snapshot = AudioConnectionSnapshot.from_dict(data)
        self.assertEqual(snapshot, rebuilt_snapshot)

        # Reconstitution to domain connection
        restored_conn = AudioConnection.from_snapshot(rebuilt_snapshot, self.library)
        self.assertEqual(restored_conn, conn)
        self.assertEqual(rebuilt_snapshot.to_connection(self.library), conn)

    def test_cue_snapshot_roundtrip(self):
        conn1 = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn2 = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])
        cue = Cue(name="Solo", connections=[conn1, conn2])

        snapshot = cue.to_snapshot()
        self.assertEqual(snapshot.name, "Solo")
        self.assertEqual(len(snapshot.connections), 2)
        self.assertIsInstance(snapshot.connections, tuple)

        # Immutability
        with self.assertRaises(Exception):
            setattr(snapshot, "name", "Mutated")

        # Dict serialization / deserialization
        data = snapshot.to_dict()
        self.assertEqual(data["name"], "Solo")
        self.assertEqual(len(data["connections"]), 2)

        rebuilt_snapshot = CueSnapshot.from_dict(data)
        self.assertEqual(snapshot, rebuilt_snapshot)

        # Reconstitution to domain cue
        restored_cue = Cue.from_snapshot(rebuilt_snapshot, self.library)
        self.assertEqual(restored_cue.name, "Solo")
        self.assertEqual(restored_cue.connections, [conn1, conn2])
        self.assertEqual(rebuilt_snapshot.to_cue(self.library).connections, [conn1, conn2])

    def test_cue_list_snapshot_roundtrip(self):
        conn1 = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        cue1 = Cue(name="Verse", connections=[conn1])
        cue2 = Cue(name="Chorus", connections=[])
        cue_list = CueList(cues=[cue1, cue2], current_index=1)

        snapshot = cue_list.to_snapshot()
        self.assertEqual(len(snapshot.cues), 2)
        self.assertEqual(snapshot.current_index, 1)
        self.assertIsInstance(snapshot.cues, tuple)

        # Immutability
        with self.assertRaises(Exception):
            setattr(snapshot, "current_index", 0)

        # Dict serialization / deserialization
        data = snapshot.to_dict()
        rebuilt_snapshot = CueListSnapshot.from_dict(data)
        self.assertEqual(snapshot, rebuilt_snapshot)

        # Reconstitution to domain cue list
        restored_list = CueList.from_snapshot(rebuilt_snapshot, self.library)
        self.assertEqual(len(restored_list), 2)
        self.assertEqual(restored_list.current_index, 1)
        self.assertEqual(restored_list[0].name, "Verse")
        self.assertEqual(restored_list[0].connections, [conn1])
        self.assertEqual(restored_list[1].name, "Chorus")
        self.assertEqual(restored_list[1].connections, [])
        self.assertEqual(len(rebuilt_snapshot.to_cue_list(self.library)), 2)

    def test_snapshot_reconstitution_error_handling(self):
        # Missing source instrument
        invalid_src_snap = AudioConnectionSnapshot(
            source_instrument="GhostSynth",
            source_port="Out1",
            target_instrument="EffectB",
            target_port="In1",
        )
        with self.assertRaises(ValueError) as ctx:
            AudioConnection.from_snapshot(invalid_src_snap, self.library)
        self.assertIn("Source instrument 'GhostSynth' not found", str(ctx.exception))

        # Missing target instrument
        invalid_tgt_snap = AudioConnectionSnapshot(
            source_instrument="SynthA",
            source_port="Out1",
            target_instrument="GhostEffect",
            target_port="In1",
        )
        with self.assertRaises(ValueError) as ctx:
            AudioConnection.from_snapshot(invalid_tgt_snap, self.library)
        self.assertIn("Target instrument 'GhostEffect' not found", str(ctx.exception))

        # Missing port
        invalid_port_snap = AudioConnectionSnapshot(
            source_instrument="SynthA",
            source_port="NonExistentPort",
            target_instrument="EffectB",
            target_port="In1",
        )
        with self.assertRaises(ValueError) as ctx:
            AudioConnection.from_snapshot(invalid_port_snap, self.library)
        self.assertIn("Output port 'NonExistentPort' not found", str(ctx.exception))

    def test_cue_transition_differential_routing_no_router_reset(self):
        # Setup: Create connections
        # conn1: SynthA:Out1 -> EffectB:In1 (sys:out1 -> sys:in2)
        # conn2: EffectB:Out1 -> MasterC:In1 (sys:out3 -> sys:in4)
        # conn3: SynthA:Out2 -> EffectB:In2 (sys:out2 -> sys:in3)
        conn1 = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn2 = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])
        conn3 = AudioConnection(self.inst_a, self.inst_a.outputs[1], self.inst_b, self.inst_b.inputs[1])

        # Cue 1 has conn1 and conn2
        cue1 = self.cue_list.create_cue_from_connections([conn1, conn2], name="Cue 1")
        # Cue 2 has conn1 and conn3 (conn1 is shared, conn2 is removed, conn3 is added)
        cue2 = self.cue_list.create_cue_from_connections([conn1, conn3], name="Cue 2")

        # Initial activation of Cue 1
        self.manage_cues.go_to_first_cue()
        self.assertEqual(self.mock_audio.remove_all_calls, 0)
        self.assertEqual(len(self.patcher.connections), 2)
        self.assertIn(conn1, self.patcher.connections)
        self.assertIn(conn2, self.patcher.connections)

        # Clear mock call histories to inspect only transition calls
        self.mock_audio.connect_calls.clear()
        self.mock_audio.disconnect_calls.clear()
        self.mock_audio.remove_all_calls = 0

        # Transition from Cue 1 to Cue 2
        self.manage_cues.go_to_next_cue()

        # Assert no full router reset occurred
        self.assertEqual(self.mock_audio.remove_all_calls, 0)

        # Assert conn2 was disconnected, conn3 was connected, and shared conn1 was untouched
        self.assertEqual(self.mock_audio.disconnect_calls, [("sys:out3", "sys:in4")])
        self.assertEqual(self.mock_audio.connect_calls, [("sys:out2", "sys:in3")])

        # Verify active router connections and patcher connections
        self.assertIn(("sys:out1", "sys:in2"), self.mock_audio.connections)
        self.assertIn(("sys:out2", "sys:in3"), self.mock_audio.connections)
        self.assertNotIn(("sys:out3", "sys:in4"), self.mock_audio.connections)
        self.assertEqual(len(self.patcher.connections), 2)
        self.assertIn(conn1, self.patcher.connections)
        self.assertIn(conn3, self.patcher.connections)


if __name__ == "__main__":
    unittest.main()
