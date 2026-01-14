from pprint import pp
import subprocess
import time
import re

import jack
import mido


_RE = re.compile(r'card ([0-9]+)[^\[]+\[([^\]]+)')


print("Detecting Fireface...")
detected_number = ""
output = subprocess.check_output(["aplay", "-l"]).decode()
for result in _RE.findall(output):
    number, name = result
    if "fireface" in name.lower():
        detected_number = number
        print("Detected interface number " + detected_number)
        break

if detected_number == "":
    raise RuntimeError("Could not detect Fireface with aplay -l")


print("Starting JACK...")
subprocess.check_output(["jack_control", "ds", "alsa"])
subprocess.check_output(["jack_control", "dps", "device", "hw:" + detected_number])
# Set buffer size and periods per buffer to achieve low latency (defaults to 1024/2048)
subprocess.check_output(["jack_control", "dps", "period", "128"])
subprocess.check_output(["jack_control", "dps", "nperiods", "3"])
subprocess.check_output(["jack_control", "start"])

print("Starting Overwitch...")
subprocess.check_output(["systemctl", "--user", "restart", "overwitch"])
time.sleep(1)
#print(subprocess.check_output(["systemctl", "--user", "status", "overwitch"]).decode())


client = jack.Client("Frangilive")
client.activate()

client.inports.register('Syntakt:Main L')

#print("JACK audio ports")
#pp(client.get_ports(is_audio=True))

#print("JACK MIDI ports")
#pp(client.get_ports(is_midi=True))

try:
    client.connect('Digitone:Main L', 'system:playback_1')
    client.connect('Digitone:Main R', 'system:playback_2')

    client.connect('Syntakt:Main L', 'system:playback_1')
    client.connect('Syntakt:Main R', 'system:playback_2')

    client.connect('Digitakt:Main L', 'system:playback_1')
    client.connect('Digitakt:Main R', 'system:playback_2')

except jack.JackError:
    raise IOError("Could not connect JACK ports. Are your synths powered on and connected ?")

finally:
    client.deactivate()

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
