# Frangilive

Frangilive live setup controller.

## Setup & Running with UV

### Development Setup (Windows / Mock Mode)
Install core dependencies for local development:
```bash
uv sync
```

### Hardware Deployment (Linux / Raspberry Pi)

Install full dependencies including JACK and MIDI hardware drivers:

```bash
source ./install.sh
```

```bash
uv sync --extra pi
```

Build the native JACK matrix from the project root (also rebuild it after updating its sources):

```bash
make -C native
```

The application starts the matrix after JACK, connects configured device ports to it, and applies patch changes with a 5 ms fade. Audio is processed entirely in the native JACK client. Device wiring is retried when ports appear; the matrix supports up to 128 distinct source and 128 distinct destination channels. The native tests can be run with `make -C native test`.

### Running the Application
Run the headless patcher / MIDI forwarder:
```bash
uv run python main.py
```

Run the Qt UI:
```bash
uv run python -m frangilive.ui
```

### Releases

GitHub Actions builds the Qt application for Linux ARM64. Pull requests and manual runs provide downloadable workflow artifacts; pushing a `v*` tag publishes them as release assets.

The Linux ARM64 archive targets 64-bit Raspberry Pi OS Bookworm or newer (glibc 2.35 or newer); 32-bit Raspberry Pi OS is not supported. Extract the complete archive and run `frangilive-app/frangilive-app` from a writable working directory. Linux archives include the native JACK matrix; JACK, `jack_control`, audio/MIDI hardware and any required Overwitch service must still be installed and configured on the host. Cue data is saved as `cues.json` in the working directory.
