from frangilive.audio.instrument import AudioInstrument
from frangilive.audio.port import AudioPort
from frangilive.device.device_library import DeviceLibrary


if __name__ == "__main__":
    output_file = "../devices.json"

    device_library = DeviceLibrary(
        name="Frangilive",
        audio_instruments=[
            AudioInstrument(
                name="Microphone",
                outputs=[
                    AudioPort("Out", "system:capture_1"),
                ]
            ),
            AudioInstrument(
                name="Main LR",
                inputs=[
                    AudioPort("Main LR", "system:playback_1", "system:playback_2"),
                ]
            ),
            AudioInstrument(
                name="MF-101",
                inputs=[
                    AudioPort("Main L", "system:playback_5"),
                ],
                outputs=[
                    AudioPort("Main L", "system:capture_2"),
                ]
            ),
            AudioInstrument(
                name="MuRF",
                inputs=[
                    AudioPort("Main L", "system:playback_6"),
                ],
                outputs=[
                    AudioPort("Main LR", "system:capture_3", "system:capture_4"),
                ]
            ),
            AudioInstrument(
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
            ),
            AudioInstrument(
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
            ),
            AudioInstrument(
                name="Digitone",
                outputs=[
                    AudioPort("Main LR", "Digitone:Main L", "Digitone:Main R"),
                    AudioPort("Track 1", "Digitone:Track 1"),
                    AudioPort("Track 2", "Digitone:Track 2"),
                    AudioPort("Track 3", "Digitone:Track 3"),
                    AudioPort("Track 4", "Digitone:Track 4"),
                ]
            ),
            AudioInstrument(
                name="Time Factor",
                inputs=[
                    AudioPort("Main L", "system:playback_3")
                ],
                outputs=[
                    AudioPort("Main LR", "system:capture_7", "system:capture_8")
                ]
            ),
            AudioInstrument(
                name="Big Sky",
                inputs=[
                    AudioPort("Main L", "system:playback_4")
                ],
                outputs=[
                    AudioPort("Main LR", "system:capture_5", "system:capture_6")
                ]
            )
        ]
    )


    with open(output_file, "w") as f:
        f.write(device_library.to_json(indent=2))

    with open(output_file, "r") as f:
        d = DeviceLibrary.from_json(f.read())
        assert d == device_library
