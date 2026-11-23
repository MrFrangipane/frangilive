import json
import unittest
from pathlib import Path


class SyntaktPortsTest(unittest.TestCase):
    def test_track_ports_match_jack_names(self):
        path = Path(__file__).resolve().parents[1] / "frangilive" / "resources" / "devices.json"
        library = json.loads(path.read_text(encoding="utf-8"))
        syntakt = next(device for device in library["audio_instruments"] if device["name"] == "Syntakt")
        tracks = {port["name"]: port for port in syntakt["outputs"]}
        for number in range(1, 13):
            port = tracks[f"Track {number}"]
            self.assertEqual(port["left"], f"Syntakt:Track {number:2d}")
            self.assertIsNone(port["right"])


if __name__ == "__main__":
    unittest.main()