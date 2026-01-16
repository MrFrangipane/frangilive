import sys
import logging
from frangilive.devices.infrastructure.json_device_repository import JsonDeviceRepository
from frangilive.midi.infrastructure.mido_midi_gateway import MidoMidiGateway
from frangilive.app import FrangiliveApp

if sys.platform == "linux":
    from frangilive.audio.infrastructure.jack_audio_system import JackAudioSystem
    audio_system = JackAudioSystem()
else:
    from frangilive.audio.infrastructure.mock_audio_system import MockAudioSystem
    audio_system = MockAudioSystem()

logging.basicConfig(level=logging.INFO)

app = FrangiliveApp(
    device_repo=JsonDeviceRepository(),
    audio_router=audio_system,
    audio_engine=audio_system,
    midi_gateway=MidoMidiGateway()
)

#
# AUDIO ENGINE
#
app.manage_engine.start_engine(
    interface_name="Fireface",
    buffer_size=128,
    driver="alsa",
    connection_type="USB"
)

#
# DEMO PATCH
#
app.connect("Digitakt", "Track 8", "MF-101", "Main L")
app.connect("Syntakt", "Main LR", "MF-101", "Main L")

app.connect("MF-101", "Main L", "Time Factor", "Main L")

app.connect("Digitone", "Main LR", "Big Sky", "Main L")
app.connect("Syntakt", 'Track 12', "Big Sky", "Main L")

app.connect("Syntakt", 'Track 11', "MuRF", "Main L")

app.connect("Big Sky", "Main LR", "Main LR", "Main LR")
app.connect("Digitakt", "Main LR", "Main LR", "Main LR")
app.connect("MuRF", "Main LR", "Main LR", "Main LR")
app.connect("Time Factor", "Main LR", "Main LR", "Main LR")

#
# MIDI
#
print("Starting MIDI forwarding...")
print("Press Ctrl-C to exit")

app.forward_midi.execute(
    input_prefix="Elektron Digitakt:Elektron Digitakt MIDI",
    output_prefixes=[
        "Elektron Syntakt:Elektron Syntakt MIDI",
        "Elektron Digitone:Elektron Digitone MIDI"
    ]
)
