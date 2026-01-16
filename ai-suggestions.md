# Project Domain: Live Audio Patching

The **Frangilive** project is a live performance audio routing system designed to run on a Raspberry Pi. Its primary goal is to manage and automate audio connections between various hardware instruments (like Elektron Digitakt, Syntakt, pedals, etc.) and a main audio interface using the **JACK Audio Connection Kit**.

### Core Domain Concepts:

- **AudioInstrument:** Represents a hardware or software device with inputs and outputs.
- **AudioPort:** Represents a specific input or output on an instrument, which can be mono or stereo (mapped to underlying JACK ports).
- **AudioConnection:** A logical link between an output port of one instrument and an input port of another.
- **DeviceLibrary:** A catalog of known instruments and their port configurations, defined in devices.json.
- **Patching:** The act of connecting/disconnecting instruments to route audio signals for a performance.

## Current Architecture

The project follows a layered architecture, though some layers are currently tightly coupled:

### 1. Domain Layer (`frangilive.instrument`, `frangilive.device`, `frangilive.patcher`):
  - Defines the entities: `AudioInstrument`, `AudioPort`, `AudioConnection`.
  - `Patcher` acts as an application service that maintains the state of active connections.

### 2. Infrastructure Layer (frangilive.audio):
  - `AbstractAudioRouter`: An interface for the audio backend.
  - `RaspberryPiAudioRouter`: The concrete implementation that talks to the Linux system (aplay, jack_control, systemctl for Overwitch) and uses the jack Python library to make actual connections.
  - `MockAudioRouter`: A stub for development on non-Linux systems.

### 3. UI Layer (frangilive.ui):
  - Built with **PySide6**.
  - `PatcherWidget`: A graphical patchbay where users can select instruments and ports to create connections.
  - It uses signals to communicate actions back to the `AudioRouter`.

### 4. Entry Points:
  - `main.py`: A CLI-based demo/test script for routing and MIDI forwarding.
  - `frangilive/ui/__main__.py`: The main GUI application.

## Suggested Improvements

To move towards a more robust, **Domain-Driven Design (DDD)** and improve object responsibility, I suggest the following changes:

### 1. Domain Representation & Rich Models

- **Introduce a `Patch` Entity:** Currently, connections are managed as a simple list in `Patcher`. A `Patch` object should represent a complete configuration of connections that can be named, saved, and loaded.
- **Rich `AudioConnection`:** Instead of passing `AudioConnectionInfo` (which is just a collection of strings) to the router, pass the rich `AudioConnection` domain object. This prevents the Infrastructure layer from having to re-resolve instruments and ports from the library.
- **Stereo vs. Mono Handling:** Move the logic for mapping mono-to-stereo or stereo-to-mono connections into the Domain layer (e.g., in a `RoutingService`) rather than having it inside the `RaspberryPiAudioRouter`.

### 2. Architecture & Object Responsibility

- **Implement a `DeviceRepository`:** As noted in your FIXME comments, centralize the loading of `devices.json`. Neither the `Patcher` nor the `AudioRouter` should be responsible for loading the JSON file. A repository should provide the `DeviceLibrary`.
- **Dependency Injection (DI):** Instead of `Patcher` and `RaspberryPiAudioRouter` creating or loading their own data, inject the `DeviceLibrary` and `AudioRouter` into them. This makes the code more testable and ensures they use the same data instance.
- **Separate Application from Infrastructure:**
  - The `Patcher` should focus on the logical state (what is connected to what).
  - The `AudioRouter` should be a "dumb" executor of port-to-port connections. It shouldn't need a `DeviceLibrary`.
  - Create a `PatchingApplicationService` that coordinates between the `Patcher` (domain state) and the `AudioRouter` (infrastructure execution).

### 3. Domain-Driven Structure (Avoid "core")

**Instead of generic modules, use names that reflect the domain:**

- `frangilive.catalog`: For `DeviceLibrary`, `DeviceRepository`, and `Instrument` definitions.
- `frangilive.routing`: For `Patch`, `Connection`, and the `AudioRouter` interface.
- `frangilive.session`: For managing the current live state, MIDI forwarding, and active patch.

### 4. Code Quality & Maintenance

- **Configuration Management:** Avoid hardcoding resource paths using `files("frangilive.resources").joinpath(...)` inside classes. Pass the path or the loaded data in during initialization.
- **Explicit State:** The `Patcher` currently maintains several lists (_instruments_with_output, etc.) that are derived from the same data. These could be computed properties or managed by a more specialized `InstrumentCatalog` class.
- **Error Handling:** The `RaspberryPiAudioRouter` uses `subprocess.check_output` without exhaustive error handling. Wrapping these in domain-specific exceptions (e.g., `AudioHardwareError`) would improve reliability.

### 5. MIDI Domain

- **MIDI Entities:** Currently, MIDI forwarding is a simple loop in `main.py`. Bringing MIDI into the domain (e.g., `MidiDevice`, `MidiRoute`) would allow the UI to manage MIDI patching as easily as audio patching.

---

_Junie prompt:_
```
- read all the codebase for project "frangilive"
- describe the project's domain and architecture
- suggest imrovements for domain representation, architecture, object responsability, etc (avoid modules like "core", stay domain-driven)
```
