import logging

import mido

from frangilive.audio.instrument import AudioInstrument
from frangilive.audio.interface_connection_type import InterfaceConnectionType
from frangilive.audio.port import AudioPort
from frangilive.audio.router.raspberry_pi import RaspberryPiAudioRouter
from frangilive.audio.router.router_factory import make_audio_router

logging.basicConfig(level=logging.INFO)

#
# AUDIO
audio_router = make_audio_router(
    buffer_size=128,
    class_=RaspberryPiAudioRouter,  # FIXME use dependency injector ?
    connection_type=InterfaceConnectionType.USB,
    driver="alsa",
    interface_name="Fireface"
)


microphone = AudioInstrument(
    name="Microphone",
    outputs=[
        AudioPort("Mic", "system:capture_1"),
    ]
)

main_out = AudioInstrument(
    name="Main out",
    inputs=[
        AudioPort("LR", "system:playback_1", "system:playback_2"),
    ]
)

mf_101 = AudioInstrument(
    name="MF-101",
    inputs=[
        AudioPort("Main L", "system:playback_5"),
    ],
    outputs=[
        AudioPort("Main L", "system:capture_2"),
    ]
)

murf = AudioInstrument(
    name="MuRF",
    inputs=[
        AudioPort("Main L", "system:playback_6"),
    ],
    outputs=[
        AudioPort("Main LR", "system:capture_3", "system:capture_4"),
    ]
)

digitakt = AudioInstrument(
    name="Digitakt",
    outputs=[
        AudioPort("Main LR", "Digitakt:Main L", "Digitakt:Main R"),
        AudioPort("Track 1", "Digitakt:Track 1"),
        AudioPort("Track 2", "Digitakt:Track 2"),
        AudioPort("Track 3", "Digitakt:Track 3"),
        AudioPort("Track 4", "Digitakt:Track 4"),
        AudioPort("Track 5", "Digitakt:Track 5"),
        AudioPort("Track 6", "Digitakt:Track 6"),
        AudioPort("Track 7", "Digitakt:Track 7"),
        AudioPort("Track 8", "Digitakt:Track 8"),
    ]
)

syntakt = AudioInstrument(
    name="Syntakt",
    outputs=[
        AudioPort("Main LR", "Syntakt:Main L", "Syntakt:Main R"),
        AudioPort("Track 1", "Syntakt:Track 1"),
        AudioPort("Track 2", "Syntakt:Track 2"),
        AudioPort("Track 3", "Syntakt:Track 3"),
        AudioPort("Track 4", "Syntakt:Track 4"),
        AudioPort("Track 5", "Syntakt:Track 5"),
        AudioPort("Track 6", "Syntakt:Track 6"),
        AudioPort("Track 7", "Syntakt:Track 7"),
        AudioPort("Track 8", "Syntakt:Track 8"),
        AudioPort("Track 9", "Syntakt:Track 9"),
        AudioPort("Track 10", "Syntakt:Track 10"),
        AudioPort("Track 11", "Syntakt:Track 11"),
        AudioPort("Track 12", "Syntakt:Track 12"),
    ]
)

digitone = AudioInstrument(
    name="Digitone",
    outputs=[
        AudioPort("Main LR", "Digitone:Main L", "Digitone:Main R"),
        AudioPort("Track 1", "Digitone:Track 1"),
        AudioPort("Track 2", "Digitone:Track 2"),
        AudioPort("Track 3", "Digitone:Track 3"),
        AudioPort("Track 4", "Digitone:Track 4"),
    ]
)

time_factor = AudioInstrument(
    name="Time Factor",
    inputs=[
        AudioPort("Main L", "system:playback_3")
    ],
    outputs=[
        AudioPort("Main LR", "system:capture_7", "system:capture_8")
    ]
)

big_sky = AudioInstrument(
    name="Big Sky",
    inputs=[
        AudioPort("Main L", "system:playback_4")
    ],
    outputs=[
        AudioPort("Main LR", "system:capture_5", "system:capture_6")
    ]
)

audio_router.connect(digitakt.output("Track 8"), mf_101.input("Main L"))
audio_router.connect(syntakt.output("Main LR"), mf_101.input("Main L"))

audio_router.connect(mf_101.output("Main L"), time_factor.input("Main L"))

audio_router.connect(digitone.output("Main LR"), big_sky.input("Main L"))
audio_router.connect(syntakt.output('Track 12'), big_sky.input("Main L"))

audio_router.connect(syntakt.output('Track 11'), murf.input("Main L"))

audio_router.connect(big_sky.output("Main LR"), main_out.input("LR"))
audio_router.connect(digitakt.output("Main LR"), main_out.input("LR"))
audio_router.connect(murf.output('Main LR'), main_out.input("LR"))
audio_router.connect(time_factor.output("Main LR"), main_out.input("LR"))

#
# MIDI
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
