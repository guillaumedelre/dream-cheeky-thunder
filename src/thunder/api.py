"""FastAPI application exposing the launcher over HTTP.

The device and launcher are module-level singletons: one shared instance
per server process. This is intentional — the physical launcher is a
single resource that cannot be controlled by two requests simultaneously
(the Launcher's asyncio.Lock enforces this at the command level).
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles

from .device import DeviceNotFoundError, ThunderDevice
from .launcher import Launcher, LauncherState, NotEnoughMissilesError

_device = ThunderDevice()
_launcher = Launcher(_device)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(_device.connect)
    except DeviceNotFoundError as exc:
        raise RuntimeError(str(exc)) from exc
    yield
    await asyncio.to_thread(_device.disconnect)


app = FastAPI(
    title="Dream Cheeky Thunder API",
    version="1.0.0",
    lifespan=_lifespan,
)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", summary="UI", include_in_schema=False)
def index():
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/status", summary="Device status")
def get_status() -> LauncherState:
    """Return the current device state: connection status, missile count, and estimated angles."""
    return _launcher.state


@app.post("/park", summary="Park the launcher at the bottom-left hard stop")
async def park() -> LauncherState:
    """Drive the launcher to its physical home position, resetting estimated angles."""
    await _launcher.park()
    return _launcher.state


@app.post("/move/{direction}", summary="Raw directional move for a given duration")
async def move(direction: str, duration: int = Query(default=500, ge=50, le=5000)) -> LauncherState:
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
async def yaw(angle: int) -> LauncherState:
    """
    Rotate the launcher to the given horizontal angle.
    The angle is clamped to the physical range [-135, 135].
    Movement is relative to the last known position; call `/park` first for accuracy.
    """
    await _launcher.yaw(angle)
    return _launcher.state


@app.post("/pitch/{angle}", summary="Tilt vertically to a target angle (-5 to 45)")
async def pitch(angle: int) -> LauncherState:
    """
    Tilt the launcher to the given vertical angle.
    The angle is clamped to the physical range [-5, 45].
    Movement is relative to the last known position; call `/park` first for accuracy.
    """
    await _launcher.pitch(angle)
    return _launcher.state


@app.post("/fire", summary="Fire N shots")
async def fire(shots: int = 1) -> LauncherState:
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
async def led(on: bool) -> LauncherState:
    """Turn the blue LED ring on (`on=true`) or off (`on=false`)."""
    await _launcher.led(on)
    return _launcher.state


@app.post("/reload", summary="Reset missile count after manual reload")
async def reload() -> LauncherState:
    """
    Notify the server that the launcher has been physically reloaded.
    Resets the missile counter to 4. Does not move the launcher.
    """
    await _launcher.reload()
    return _launcher.state
