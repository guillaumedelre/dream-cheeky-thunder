# Development

## Architecture

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

## Running without Docker

Requires [uv](https://docs.astral.sh/uv/) and the platform setup completed first:

- **Linux**: udev rule installed (see [setup-linux.md](setup-linux.md))
- **Windows**: udev rule installed and usbipd attached (see [setup-windows-wsl2.md](setup-windows-wsl2.md))

```bash
uv sync
uv run uvicorn thunder.api:app --reload
```

The server starts at `http://localhost:8000`.
