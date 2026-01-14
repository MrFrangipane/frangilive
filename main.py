import logging

import mido

from frangilive.audio.interface_connection_type import InterfaceConnectionType
from frangilive.audio.router.raspberry_pi import RaspberryPiAudioRouter
from frangilive.audio.router.router_factory import make_audio_router
from frangilive.device.device_library import DeviceLibrary

logging.basicConfig(level=logging.INFO)

#
# DEVICES
with open("../devices.json", "r") as f:
    device_library = DeviceLibrary.from_json(f.read())

digitakt = device_library.audio_instrument("Digitakt")
digitone = device_library.audio_instrument("Digitone")
syntakt = device_library.audio_instrument("Syntakt")

big_sky = device_library.audio_instrument("Big Sky")
mf_101 = device_library.audio_instrument("MF-101")
murf = device_library.audio_instrument("MuRF")
time_factor = device_library.audio_instrument("Time Factor")

main_out = device_library.audio_instrument("Out")

#
# AUDIO ROUTER
audio_router = make_audio_router(
    buffer_size=128,
    class_=RaspberryPiAudioRouter,  # FIXME use dependency injector ?
    connection_type=InterfaceConnectionType.USB,
    driver="alsa",
    interface_name="Fireface"
)

#
# DEMO PATCH
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


print("Press Ctrl-C to exit")
forward_midi()
