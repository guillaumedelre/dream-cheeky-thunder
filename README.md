# dream-cheeky-thunder

REST API to control the [Dream Cheeky USB missile launcher](http://www.dreamcheeky.com/thunder-missile-launcher).

## Requirements

- Docker + Docker Compose
- The launcher connected via USB

## Quick start

### Linux

Install the udev rule once to allow non-root USB access:

```bash
sudo cp udev/99-dream-cheeky.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Start the server:

```bash
docker compose up
```

### Windows (Docker Desktop + WSL2)

1. Install [usbipd-win](https://github.com/dorssel/usbipd-win)
2. List USB devices and attach the launcher to WSL2 (run in PowerShell as Administrator):

```powershell
usbipd list
usbipd attach --wsl --busid <BUSID>
```

3. Start the server from WSL2:

```bash
docker compose up
```

To detach after use:

```powershell
usbipd detach --busid <BUSID>
```

## API

The API is available at `http://localhost:8000`.
Interactive docs (Swagger UI): `http://localhost:8000/docs`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Device status (missiles, angles) |
| POST | `/park` | Move to home position (bottom-left) |
| POST | `/move/{direction}?duration=500` | Raw move: `up`, `down`, `left`, `right` |
| POST | `/yaw/{angle}` | Rotate horizontally (-135 to 135 degrees) |
| POST | `/pitch/{angle}` | Tilt vertically (-5 to 45 degrees) |
| POST | `/fire?shots=1` | Fire N shots |
| POST | `/led?on=true` | Toggle the LED |
| POST | `/reload` | Reset missile count after manual reload |

### Example

```bash
# Park
curl -X POST http://localhost:8000/park

# Aim center, slightly up
curl -X POST http://localhost:8000/yaw/0
curl -X POST http://localhost:8000/pitch/20

# Fire 2 shots
curl -X POST "http://localhost:8000/fire?shots=2"
```

## Device constants

| Parameter | Value |
|-----------|-------|
| Vendor ID | `0x2123` |
| Product ID | `0x1010` |
| Yaw range | -135° to 135° |
| Pitch range | -5° to 45° |
| Missile capacity | 4 |

> Angle tracking is time-based and approximate. Run `/park` to reset to a known position before precise targeting.
