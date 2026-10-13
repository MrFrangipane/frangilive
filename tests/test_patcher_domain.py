import unittest
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.domain.audio_port import AudioPort
from frangilive.devices.domain.device_library import DeviceLibrary
from frangilive.patcher.domain.audio_connection import AudioConnection
from frangilive.patcher.domain.patcher import Patcher, CyclicConnectionError
from frangilive.patcher.application.manage_connections import ManageConnectionsUseCase
from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem


class TestPatcherAcyclicity(unittest.TestCase):

    def setUp(self):
        self.inst_a = AudioInstrument(
            name="SynthA",
            inputs=[AudioPort(name="In1", left="sys:in1")],
            outputs=[AudioPort(name="Out1", left="sys:out1"), AudioPort(name="Out2", left="sys:out2")]
        )
        self.inst_b = AudioInstrument(
            name="EffectB",
            inputs=[AudioPort(name="In1", left="sys:in2"), AudioPort(name="In2", left="sys:in3")],
            outputs=[AudioPort(name="Out1", left="sys:out3")]
        )
        self.inst_c = AudioInstrument(
            name="MixerC",
            inputs=[AudioPort(name="In1", left="sys:in4")],
            outputs=[AudioPort(name="Out1", left="sys:out4")]
        )
        self.inst_d = AudioInstrument(
            name="MasterD",
            inputs=[AudioPort(name="In1", left="sys:in5")],
            outputs=[]
        )
        self.library = DeviceLibrary(
            name="TestLib",
            audio_instruments=[self.inst_a, self.inst_b, self.inst_c, self.inst_d]
        )
        self.patcher = Patcher(device_library=self.library)

    def test_empty_patcher_is_acyclic(self):
        self.assertTrue(self.patcher.is_acyclic())
        self.assertFalse(self.patcher.has_cycle())

    def test_linear_connection_chain_is_acyclic(self):
        conn_ab = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn_bc = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])
        conn_cd = AudioConnection(self.inst_c, self.inst_c.outputs[0], self.inst_d, self.inst_d.inputs[0])

        self.patcher.add_connection(conn_ab)
        self.patcher.add_connection(conn_bc)
        self.patcher.add_connection(conn_cd)

        self.assertTrue(self.patcher.is_acyclic())
        self.assertFalse(self.patcher.has_cycle())
        self.assertEqual(len(self.patcher.connections), 3)

    def test_branching_dag_is_acyclic(self):
        # A -> B, A -> C, B -> D, C -> D (diamond topology)
        conn_ab = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn_ac = AudioConnection(self.inst_a, self.inst_a.outputs[1], self.inst_c, self.inst_c.inputs[0])
        conn_bd = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_d, self.inst_d.inputs[0])

        self.patcher.add_connection(conn_ab)
        self.patcher.add_connection(conn_ac)
        self.patcher.add_connection(conn_bd)

        self.assertTrue(self.patcher.is_acyclic())

    def test_multiple_connections_between_same_instruments_is_acyclic(self):
        # A(Out1) -> B(In1) and A(Out2) -> B(In2)
        conn1 = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn2 = AudioConnection(self.inst_a, self.inst_a.outputs[1], self.inst_b, self.inst_b.inputs[1])

        self.patcher.add_connection(conn1)
        self.patcher.add_connection(conn2)

        self.assertTrue(self.patcher.is_acyclic())
        self.assertEqual(len(self.patcher.connections), 2)

    def test_self_connection_rejected(self):
        # A -> A
        conn_self = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_a, self.inst_a.inputs[0])

        self.assertTrue(self.patcher.would_create_cycle(conn_self))
        self.assertFalse(self.patcher.can_add_connection(conn_self))

        with self.assertRaises(CyclicConnectionError):
            self.patcher.add_connection(conn_self)

        self.assertEqual(len(self.patcher.connections), 0)

    def test_direct_two_node_cycle_rejected(self):
        # A -> B then B -> A
        conn_ab = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn_ba = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_a, self.inst_a.inputs[0])

        self.patcher.add_connection(conn_ab)

        self.assertTrue(self.patcher.would_create_cycle(conn_ba))
        self.assertFalse(self.patcher.can_add_connection(conn_ba))

        with self.assertRaises(CyclicConnectionError):
            self.patcher.add_connection(conn_ba)

        self.assertEqual(len(self.patcher.connections), 1)

    def test_indirect_three_node_cycle_rejected(self):
        # A -> B -> C then C -> A
        conn_ab = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn_bc = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])
        conn_ca = AudioConnection(self.inst_c, self.inst_c.outputs[0], self.inst_a, self.inst_a.inputs[0])

        self.patcher.add_connection(conn_ab)
        self.patcher.add_connection(conn_bc)

        self.assertTrue(self.patcher.would_create_cycle(conn_ca))
        self.assertFalse(self.patcher.can_add_connection(conn_ca))

        with self.assertRaises(CyclicConnectionError):
            self.patcher.add_connection(conn_ca)

        self.assertEqual(len(self.patcher.connections), 2)

    def test_cyclic_connection_error_is_value_error(self):
        self.assertTrue(issubclass(CyclicConnectionError, ValueError))

    def test_post_init_detects_initial_cycle(self):
        conn_ab = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn_ba = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_a, self.inst_a.inputs[0])

        with self.assertRaises(CyclicConnectionError):
            Patcher(device_library=self.library, connections=[conn_ab, conn_ba])

    def test_removing_connection_allows_previously_cyclic_connection(self):
        # A -> B -> C
        conn_ab = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        conn_bc = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])
        conn_ca = AudioConnection(self.inst_c, self.inst_c.outputs[0], self.inst_a, self.inst_a.inputs[0])

        self.patcher.add_connection(conn_ab)
        self.patcher.add_connection(conn_bc)

        # C -> A would form a cycle
        self.assertTrue(self.patcher.would_create_cycle(conn_ca))

        # Remove A -> B
        self.patcher.remove_connection(conn_ab)

        # Now C -> A is valid because B is no longer fed by A
        self.assertFalse(self.patcher.would_create_cycle(conn_ca))
        self.patcher.add_connection(conn_ca)
        self.assertTrue(self.patcher.is_acyclic())

    def test_manage_connections_use_case_prevents_cycles(self):
        mock_audio = MockAudioSystem()
        use_case = ManageConnectionsUseCase(router_gateway=mock_audio, patcher=self.patcher)

        # Connect SynthA -> EffectB
        self.assertTrue(use_case.connect("SynthA", "Out1", "EffectB", "In1"))

        # Connect EffectB -> MixerC
        self.assertTrue(use_case.connect("EffectB", "Out1", "MixerC", "In1"))

        # Attempt to connect MixerC -> SynthA (cycle)
        self.assertFalse(use_case.connect("MixerC", "Out1", "SynthA", "In1"))

        # Attempt self-connection SynthA -> SynthA
        self.assertFalse(use_case.connect("SynthA", "Out1", "SynthA", "In1"))

        self.assertEqual(len(self.patcher.connections), 2)

    def test_would_create_cycle_between_by_names(self):
        # Empty graph: SynthA -> EffectB is acyclic
        self.assertFalse(self.patcher.would_create_cycle_between("SynthA", "EffectB"))
        # Self connection would create cycle
        self.assertTrue(self.patcher.would_create_cycle_between("SynthA", "SynthA"))

        # Add SynthA -> EffectB
        conn_ab = AudioConnection(self.inst_a, self.inst_a.outputs[0], self.inst_b, self.inst_b.inputs[0])
        self.patcher.add_connection(conn_ab)

        # Adding another connection in same direction SynthA -> EffectB is acyclic
        self.assertFalse(self.patcher.would_create_cycle_between("SynthA", "EffectB"))
        # Reverse EffectB -> SynthA would create cycle
        self.assertTrue(self.patcher.would_create_cycle_between("EffectB", "SynthA"))

        # Add EffectB -> MixerC
        conn_bc = AudioConnection(self.inst_b, self.inst_b.outputs[0], self.inst_c, self.inst_c.inputs[0])
        self.patcher.add_connection(conn_bc)

        # Indirect cycle MixerC -> SynthA would create cycle
        self.assertTrue(self.patcher.would_create_cycle_between("MixerC", "SynthA"))
        # Forward SynthA -> MixerC is acyclic
        self.assertFalse(self.patcher.would_create_cycle_between("SynthA", "MixerC"))


if __name__ == "__main__":
    unittest.main()
