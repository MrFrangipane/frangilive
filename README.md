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

### Running the Application
Run the headless patcher / MIDI forwarder:
```bash
uv run python main.py
```

Run the Qt UI:
```bash
uv run python -m frangilive.ui
```
