# API Reference

Interactive documentation (Swagger UI) is available at `http://localhost:8000/docs` while the server is running.

## Response format

All endpoints return the current device state as JSON:

```json
{
  "connected": true,
  "missiles": 4,
  "yaw": 0,
  "pitch": 0
}
```

`connected` reflects whether the server currently has an open USB connection to the launcher. Hardware endpoints return HTTP 503 if the device is not present.

## Endpoints

| Method | Path | Query params | Description |
|--------|------|--------------|-------------|
| GET | `/` | | Web UI |
| GET | `/status` | | Current device state |
| POST | `/park` | | Drive to home position (bottom-left hard stop) |
| POST | `/move/{direction}` | `duration` (ms, default 500) | Raw move: `up`, `down`, `left`, `right` |
| POST | `/yaw/{angle}` | | Rotate to horizontal angle (-135 to 135) |
| POST | `/pitch/{angle}` | | Tilt to vertical angle (-5 to 45) |
| POST | `/fire` | `shots` (default 1) | Fire N shots sequentially |
| POST | `/led` | `on` (`true`/`false`) | Toggle the LED ring |
| POST | `/reload` | | Reset missile count after manual reload |

## Examples

```bash
# Check device status
curl http://localhost:8000/status

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

## Position tracking

Angle tracking is time-based and approximate. The server estimates the current angle by recording how long the motors have been running. Accuracy degrades if the launcher is bumped or a command is interrupted.

Call `POST /park` before any precision targeting sequence: it drives the motors against the physical hard stops for the full sweep duration, guaranteeing alignment regardless of the estimated position.
