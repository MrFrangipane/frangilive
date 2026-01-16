import logging
from frangilive.midi.interfaces.midi import MidiGateway

_logger = logging.getLogger(__name__)


class ForwardMidiUseCase:
    def __init__(self, midi_gateway: MidiGateway):
        self.midi_gateway = midi_gateway

    def execute(self, input_prefix: str, output_prefixes: list[str]):
        _logger.info(f"Starting MIDI forwarding from {input_prefix} to {output_prefixes}")
        midi_in = self.midi_gateway.open_input(input_prefix)
        midi_outs = [self.midi_gateway.open_output(prefix) for prefix in output_prefixes]

        try:
            while True:
                msg = midi_in.receive()
                if msg:
                    for midi_out in midi_outs:
                        midi_out.send(msg)
        except (KeyboardInterrupt, Exception) as e:
            _logger.info(f"Stopping MIDI forwarding: {e}")
        finally:
            self.midi_gateway.close_all()
