# Development

## 🏗️ Architecture

```
src/thunder/
├── constants.py      Hardware constants: USB IDs, angle ranges, command bytes
├── device.py         USB communication via pyusb + libusb (only layer touching raw USB)
├── launcher.py       High-level commands: move, yaw, pitch, fire, park
├── api.py            FastAPI routes, one instance of Launcher shared across requests
└── static/
    └── index.html    Web UI served at /
```

The layers are intentionally separated: `device.py` knows only about bytes and transfers; `launcher.py` knows about angles, timing, and state; `api.py` knows about HTTP.

## 🔌 USB protocol

All communication goes through HID `SET_REPORT` control transfers (`bmRequestType=0x21`, `bRequest=0x09`). The payload is always 8 bytes.

**Movement and fire** use report ID `0x02` (byte 0 of the payload):

```
[0x02, cmd, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
```

| `cmd` | Action |
|-------|--------|
| `0x01` | ⬇️ Move down |
| `0x02` | ⬆️ Move up |
| `0x04` | ⬅️ Move left |
| `0x08` | ➡️ Move right |
| `0x10` | 🚀 Fire |
| `0x20` | ⏹️ Stop |

**LED** uses a distinct report ID `0x03` — it cannot be sent via the movement report:

```
[0x03, state, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
```

`state`: `0x01` = on, `0x00` = off.

## 📍 Position tracking

The device has no position feedback. `launcher.py` estimates angles by timing motor runs against calibrated ms-per-degree constants. Accuracy degrades after raw `move` calls or physical bumps. `park()` recovers a known position by driving both axes against their hard stops for the full sweep duration.

## 🚀 Running without Docker

Requires [uv](https://docs.astral.sh/uv/) and the platform setup completed first:

- 🐧 **Linux**: udev rule installed (see [setup-linux.md](setup-linux.md))
- 🪟 **Windows**: udev rule installed and usbipd attached (see [setup-windows-wsl2.md](setup-windows-wsl2.md))

```bash
uv sync
uv run uvicorn thunder.api:app --reload
```

The server starts at `http://localhost:8000`.
