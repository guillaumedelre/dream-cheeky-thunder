from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from .device import DeviceNotFoundError, ThunderDevice
from .launcher import Launcher, NotEnoughMissilesError

_device = ThunderDevice()
_launcher = Launcher(_device)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _device.connect()
    yield
    _device.disconnect()


app = FastAPI(
    title="Dream Cheeky Thunder API",
    version="1.0.0",
    lifespan=_lifespan,
)


def _device_error_handler(exc: Exception) -> None:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@app.get("/", summary="Device status")
def get_status() -> dict:
    return _launcher.state


@app.post("/park", summary="Park the launcher (bottom-left)")
async def park() -> dict:
    await _launcher.park()
    return _launcher.state


@app.post("/move/{direction}", summary="Move in a direction for a given duration")
async def move(direction: str, duration: int = 500) -> dict:
    try:
        await _launcher.move(direction, duration)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _launcher.state


@app.post("/yaw/{angle}", summary="Rotate horizontally to a target angle (-135 to 135)")
async def yaw(angle: int) -> dict:
    await _launcher.yaw(angle)
    return _launcher.state


@app.post("/pitch/{angle}", summary="Tilt vertically to a target angle (-5 to 45)")
async def pitch(angle: int) -> dict:
    await _launcher.pitch(angle)
    return _launcher.state


@app.post("/fire", summary="Fire N shots")
async def fire(shots: int = 1) -> dict:
    try:
        await _launcher.fire(shots)
    except (ValueError, NotEnoughMissilesError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _launcher.state


@app.post("/led", summary="Toggle the LED")
def led(on: bool) -> dict:
    _launcher.led(on)
    return _launcher.state


@app.post("/reload", summary="Reset missile count after manual reload")
def reload() -> dict:
    _launcher.reload()
    return _launcher.state
