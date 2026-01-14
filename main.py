import logging

import mido

from frangilive.audiomidi.audio_port import AudioPort
from frangilive.audiomidi.instrument import Instrument
from frangilive.audiomidi.jack_options import JackOptions
from frangilive.audiomidi.raspberry_pi import RaspberryPiAudioMidi

logging.basicConfig(level=logging.INFO)

audio_midi = RaspberryPiAudioMidi()
if not audio_midi.find_audio_interface(name="fireface"):
    raise RuntimeError("No audio interface found")

audio_midi.start_jack_server(JackOptions(
    buffer_period_count=3,
    buffer_size=128,
    driver="alsa"
))
audio_midi.start_overwitch()
audio_midi.activate_jack_client()
audio_midi.remove_all_audio_connections()


fireface = Instrument(
    name="Fireface",
    inputs=[
        AudioPort("Mic", "system:capture_1"),
        AudioPort("MF-101", "system:capture_2"),
    ],
    outputs=[
        AudioPort("Main", "system:playback_1", "system:playback_2"),
        AudioPort("MF-101", "system:playback_5"),
    ]
)

digitakt = Instrument(
    name="Digitakt",
    outputs=[
        AudioPort("Main", "Digitakt:Main L", "Digitakt:Main R"),
        AudioPort("Track 8", "Digitakt:Track 8"),
    ]
)

audio_midi.connect(digitakt.output("Track 8"), fireface.output("MF-101"))
audio_midi.connect(fireface.input("MF-101"), fireface.output("Main"))


print("Starting MIDI forwarding...")

midi_inputs = mido.get_input_names()
midi_outputs = mido.get_output_names()

#print("Available input ports:")
#print("\n".join(midi_inputs))
#print("")
#print("Available output ports:")
#print("\n".join(midi_outputs))
#print("")

def find_name(name_prefix: str, names: list[str]):
    for name in names:
        if name.startswith(name_prefix):
            return name
    raise ValueError(f"No port name starting with '{name_prefix}' found.")


midi_digitakt = mido.open_input(find_name("Elektron Digitakt:Elektron Digitakt MIDI", midi_inputs))
midi_syntakt = mido.open_output(find_name("Elektron Syntakt:Elektron Syntakt MIDI", midi_outputs))
midi_digitone = mido.open_output(find_name("Elektron Digitone:Elektron Digitone MIDI", midi_outputs))


def forward_midi():
    try:
        while True:
            msg = midi_digitakt.receive()
            midi_syntakt.send(msg)
            midi_digitone.send(msg)

    except KeyboardInterrupt:
        print('Exiting')

    finally:
        midi_digitakt.close()
        midi_syntakt.close()
        midi_digitone.close()


print("Press Ctrl-C to exit.")
forward_midi()
