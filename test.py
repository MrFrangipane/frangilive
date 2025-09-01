from pprint import pp
import time

import subprocess
import mido
import jack


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

finally:
    client.deactivate()

print("Starting MIDI forwarding...")

print("Available input ports:")
print(mido.get_input_names())

print("Available output ports:")
print(mido.get_output_names())

midi_digitakt = mido.open_input('Elektron Digitakt:Elektron Digitakt MIDI 1 24:0')
midi_syntakt = mido.open_output('Elektron Syntakt:Elektron Syntakt MIDI 1 32:0')
midi_digitone = mido.open_output('Elektron Digitone:Elektron Digitone MIDI 1 28:0')

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
