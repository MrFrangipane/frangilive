import json
from importlib.resources import files, as_file
from frangilive.devices.domain.audio_port import AudioPort
from frangilive.devices.domain.audio_instrument import AudioInstrument
from frangilive.devices.domain.device_library import DeviceLibrary
from frangilive.devices.interfaces.device_repository import DeviceRepository


class JsonDeviceRepository(DeviceRepository):
    def load_library(self) -> DeviceLibrary:
        resource_path = files("frangilive.resources").joinpath("devices.json")
        with as_file(resource_path) as p:
            with open(p, "r") as f:
                data = json.load(f)

        instruments = []
        for inst_data in data.get("audio_instruments", []):
            inputs = [AudioPort(name=p["name"], left=p["left"], right=p.get("right")) for p in inst_data.get("inputs", [])]
            outputs = [AudioPort(name=p["name"], left=p["left"], right=p.get("right")) for p in inst_data.get("outputs", [])]
            instruments.append(AudioInstrument(
                name=inst_data["name"],
                inputs=inputs,
                outputs=outputs,
                default_input_name=inst_data.get("default_input_name"),
                default_output_name=inst_data.get("default_output_name"),
                icon_name=inst_data.get("icon_name")
            ))

        return DeviceLibrary(name=data["name"], audio_instruments=instruments)
