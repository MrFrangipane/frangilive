import sys
import logging
from frangilive.infrastructure.persistence.json_device_repository import JsonDeviceRepository
from frangilive.infrastructure.midi.mido_midi_gateway import MidoMidiGateway
from frangilive.application.app import FrangiliveApp

if sys.platform == "linux":
    from frangilive.infrastructure.audio.jack_audio_router import JackAudioRouter
    audio_impl = JackAudioRouter()
else:
    from frangilive.infrastructure.audio.mock_audio_router import MockAudioRouter
    audio_impl = MockAudioRouter()

logging.basicConfig(level=logging.INFO)

app = FrangiliveApp(
    device_repo=JsonDeviceRepository(),
    audio_router=audio_impl,
    audio_engine=audio_impl,
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
