import unittest
from frangilive.devices.domain.audio_port import AudioPort
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository


class TestAudioInstrument(unittest.TestCase):

    def test_default_ports_initial_resolution(self):
        inst = AudioInstrument(
            name="TestSynth",
            inputs=[AudioPort(name="In L", left="sys:in_1"), AudioPort(name="In R", left="sys:in_2")],
            outputs=[AudioPort(name="Out Main", left="sys:out_1"), AudioPort(name="Out Aux", left="sys:out_2")]
        )
        # Should resolve to first input and first output by default
        self.assertEqual(inst.get_default_input().name, "In L")
        self.assertEqual(inst.get_default_output().name, "Out Main")

    def test_customize_default_input_and_output(self):
        inst = AudioInstrument(
            name="TestSynth",
            inputs=[AudioPort(name="In L", left="sys:in_1"), AudioPort(name="In R", left="sys:in_2")],
            outputs=[AudioPort(name="Out Main", left="sys:out_1"), AudioPort(name="Out Aux", left="sys:out_2")]
        )
        inst.set_default_input("In R")
        inst.set_default_output("Out Aux")

        self.assertEqual(inst.get_default_input().name, "In R")
        self.assertEqual(inst.get_default_output().name, "Out Aux")

    def test_set_invalid_default_port_raises_value_error(self):
        inst = AudioInstrument(
            name="TestSynth",
            inputs=[AudioPort(name="In L", left="sys:in_1")],
            outputs=[AudioPort(name="Out Main", left="sys:out_1")]
        )
        with self.assertRaises(ValueError):
            inst.set_default_input("NonExistent")

        with self.assertRaises(ValueError):
            inst.set_default_output("NonExistent")

    def test_json_device_repository_loads_default_ports(self):
        repo = JsonDeviceRepository()
        lib = repo.load_library()
        self.assertGreater(len(lib.audio_instruments), 0)

        for inst in lib.audio_instruments:
            if inst.inputs:
                self.assertIsNotNone(inst.get_default_input())
            if inst.outputs:
                self.assertIsNotNone(inst.get_default_output())


if __name__ == "__main__":
    unittest.main()
