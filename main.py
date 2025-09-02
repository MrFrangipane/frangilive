from pprint import pp
import subprocess
import time

import jack
import mido


print("Starting JACK...")
subprocess.check_output(["jack_control", "start"])

print("Starting Overwitch...")
subprocess.check_output(["systemctl", "--user", "restart", "overwitch"])
time.sleep(1)
print(subprocess.check_output(["systemctl", "--user", "status", "overwitch"]).decode())


client = jack.Client("Frangilive")
client.activate()

client.inports.register('Syntakt:Main L')

print("JACK audio ports")
pp(client.get_ports(is_audio=True))

print("JACK MIDI ports")
pp(client.get_ports(is_midi=True))

try:
    client.connect('Syntakt:Main L', 'Digitone:Main L Input')
    client.connect('Syntakt:Main R', 'Digitone:Main R Input')
    
    client.connect('Digitakt:Main L', 'Digitone:Main L Input')
    client.connect('Digitakt:Main R', 'Digitone:Main R Input')

except jack.JackError:
    raise IOError("Could not connect JACK ports. Are your synths powered on and connected ?")

finally:
    client.deactivate()

print("Starting MIDI forwarding...")

midi_inputs = mido.get_input_names()
midi_outputs = mido.get_output_names()

print("Available input ports:")
print("\n".join(midi_inputs))
print("")
print("Available output ports:")
print("\n".join(midi_outputs))
print("")

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
