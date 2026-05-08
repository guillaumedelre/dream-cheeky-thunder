# dream-cheeky-thunder

A self-hosted REST API to control the [Dream Cheeky USB Thunder missile launcher](http://www.dreamcheeky.com/thunder-missile-launcher) over HTTP.

The API is built with Python and FastAPI, packaged as a Docker image. Once running, you can aim and fire the launcher from any HTTP client, script, or browser.

---

## Hardware

| Spec | Value |
|------|-------|
| USB Vendor ID | `0x2123` |
| USB Product ID | `0x1010` |
| Yaw (horizontal) | -135° to +135° |
| Pitch (vertical) | -5° to +45° |
| Missile capacity | 4 foam missiles |
| Inter-shot delay | 4.5 seconds |

> **Position tracking** is time-based and approximate. The server estimates the current angle by tracking how long the motors have been running. Physical accuracy degrades if the launcher is bumped or if commands are interrupted. Call `POST /park` before any precision targeting sequence to reset to a known physical position.

---

## Requirements

- Docker and Docker Compose
- The launcher connected via USB before starting the server

---

## Quick start

### Linux

**1. Install the udev rule** (one-time, allows USB access without root):

```bash
sudo cp udev/99-dream-cheeky.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**2. Start the server:**

```bash
docker compose up
```

The API is available at `http://localhost:8000`.

---

### Windows (Docker Desktop + WSL2)

USB passthrough to WSL2 requires [usbipd-win](https://github.com/dorssel/usbipd-win).

**1. Install usbipd-win** from the [releases page](https://github.com/dorssel/usbipd-win/releases).

**2. Attach the launcher to WSL2** (run in PowerShell as Administrator):

```powershell
# List available USB devices to find the launcher
usbipd list

# Attach it to WSL2 (replace <BUSID> with the value from the list, e.g. 1-3)
usbipd attach --wsl --busid <BUSID>
```

**3. Start the server** (from WSL2 or Docker Desktop terminal):

```bash
docker compose up
```

**4. Detach after use:**

```powershell
usbipd detach --busid <BUSID>
```

> The `usbipd attach` step must be repeated each time the device is unplugged or the system reboots.

---

## API reference

Interactive documentation (Swagger UI) is available at `http://localhost:8000/docs` while the server is running.

All endpoints return the current device state as JSON:

```json
{
  "connected": true,
  "missiles": 4,
  "yaw": 0,
  "pitch": 0
}
```

### Endpoints

| Method | Path | Query params | Description |
|--------|------|--------------|-------------|
| GET | `/` | | Current device state |
| POST | `/park` | | Drive to home position (bottom-left hard stop) |
| POST | `/move/{direction}` | `duration` (ms, default 500) | Raw move: `up`, `down`, `left`, `right` |
| POST | `/yaw/{angle}` | | Rotate to horizontal angle (-135 to 135) |
| POST | `/pitch/{angle}` | | Tilt to vertical angle (-5 to 45) |
| POST | `/fire` | `shots` (default 1) | Fire N shots sequentially |
| POST | `/led` | `on` (`true`/`false`) | Toggle the LED ring |
| POST | `/reload` | | Reset missile count after manual reload |

### Examples

```bash
# Check device status
curl http://localhost:8000/

# Park (reset to known position before targeting)
curl -X POST http://localhost:8000/park

# Aim: center horizontally, tilt up 20°
curl -X POST http://localhost:8000/yaw/0
curl -X POST http://localhost:8000/pitch/20

# Fire 2 shots
curl -X POST "http://localhost:8000/fire?shots=2"

# Move left for 1 second (raw, no angle tracking)
curl -X POST "http://localhost:8000/move/left?duration=1000"

# Turn on the LED
curl -X POST "http://localhost:8000/led?on=true"

# After physically reloading the launcher
curl -X POST http://localhost:8000/reload
```

---

## Architecture

```
src/thunder/
├── constants.py   Hardware constants: USB IDs, angle ranges, command bytes
├── device.py      USB communication via pyusb + libusb (only layer touching raw USB)
├── launcher.py    High-level commands: move, yaw, pitch, fire, park
└── api.py         FastAPI routes, one instance of Launcher shared across requests
```

The layers are intentionally separated: `device.py` knows only about bytes and transfers; `launcher.py` knows about angles, timing, and state; `api.py` knows about HTTP.

---

## Development (without Docker)

Requires [uv](https://docs.astral.sh/uv/) and the udev rule installed (Linux) or usbipd attached (Windows).

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn thunder.api:app --reload
```

---

## Troubleshooting

**Device not found on Linux**

Make sure the udev rule is installed and the device was plugged in after the rule was applied:

```bash
# Verify the device is visible to the OS
lsusb | grep 2123
```

If it does not appear, try a different USB port or cable.

**Permission denied on Linux**

If you see a `USBError: [Errno 13] Access denied` error, the udev rule may not have been applied yet:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
# Then unplug and replug the launcher
```

**Device not found on Windows**

Verify that the device is attached to WSL2 and visible from inside the container:

```bash
# From WSL2
lsusb | grep 2123
```

If it does not appear, re-run `usbipd attach --wsl --busid <BUSID>` from PowerShell.

**Launcher not moving accurately**

Time-based positioning drifts over multiple commands. Call `POST /park` to reset to the physical home position before a precision targeting sequence.
