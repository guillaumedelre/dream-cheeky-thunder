"""FastAPI application exposing the launcher over HTTP.

The device and launcher are module-level singletons: one shared instance
per server process. This is intentional — the physical launcher is a
single resource that cannot be controlled by two requests simultaneously
(the Launcher's asyncio.Lock enforces this at the command level).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from .device import ThunderDevice
from .launcher import Launcher, NotEnoughMissilesError

_device = ThunderDevice()
_launcher = Launcher(_device)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # lifespan is FastAPI's recommended startup/shutdown hook (replaces deprecated @on_event).
    # The USB connection is opened once when the server starts and closed when it stops.
    _device.connect()
    yield
    _device.disconnect()


app = FastAPI(
    title="Dream Cheeky Thunder API",
    version="1.0.0",
    lifespan=_lifespan,
)


@app.get("/", summary="Device status")
def get_status() -> dict:
    """Return the current device state: connection status, missile count, and estimated angles."""
    return _launcher.state


@app.post("/park", summary="Park the launcher at the bottom-left hard stop")
async def park() -> dict:
    """Drive the launcher to its physical home position, resetting estimated angles."""
    await _launcher.park()
    return _launcher.state


@app.post("/move/{direction}", summary="Raw directional move for a given duration")
async def move(direction: str, duration: int = 500) -> dict:
    """
    Move in a raw direction (`up`, `down`, `left`, `right`) for `duration` milliseconds.

    Does not update the estimated yaw/pitch angles. Use `/yaw` and `/pitch` for
    angle-aware positioning.
    """
    try:
        await _launcher.move(direction, duration)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _launcher.state


@app.post("/yaw/{angle}", summary="Rotate horizontally to a target angle (-135 to 135)")
async def yaw(angle: int) -> dict:
    """
    Rotate the launcher to the given horizontal angle.
    The angle is clamped to the physical range [-135, 135].
    Movement is relative to the last known position; call `/park` first for accuracy.
    """
    await _launcher.yaw(angle)
    return _launcher.state


@app.post("/pitch/{angle}", summary="Tilt vertically to a target angle (-5 to 45)")
async def pitch(angle: int) -> dict:
    """
    Tilt the launcher to the given vertical angle.
    The angle is clamped to the physical range [-5, 45].
    Movement is relative to the last known position; call `/park` first for accuracy.
    """
    await _launcher.pitch(angle)
    return _launcher.state


@app.post("/fire", summary="Fire N shots")
async def fire(shots: int = 1) -> dict:
    """
    Fire the specified number of shots sequentially.
    Returns 422 if there are not enough missiles remaining.
    """
    try:
        await _launcher.fire(shots)
    except (ValueError, NotEnoughMissilesError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _launcher.state


@app.post("/led", summary="Toggle the LED ring on the launcher base")
def led(on: bool) -> dict:
    """Turn the blue LED ring on (`on=true`) or off (`on=false`)."""
    _launcher.led(on)
    return _launcher.state


@app.post("/reload", summary="Reset missile count after manual reload")
def reload() -> dict:
    """
    Notify the server that the launcher has been physically reloaded.
    Resets the missile counter to 4. Does not move the launcher.
    """
    _launcher.reload()
    return _launcher.state
