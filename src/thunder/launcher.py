import asyncio

from .constants import (
    Cmd,
    Led,
    MISSILE_COUNT,
    PITCH_MAX_ANGLE,
    PITCH_MIN_ANGLE,
    PITCH_TOTAL_DURATION_MS,
    RELOAD_DELAY_MS,
    YAW_MAX_ANGLE,
    YAW_MIN_ANGLE,
    YAW_TOTAL_DURATION_MS,
)
from .device import ThunderDevice

_YAW_MS_PER_DEGREE = YAW_TOTAL_DURATION_MS / (YAW_MAX_ANGLE - YAW_MIN_ANGLE)
_PITCH_MS_PER_DEGREE = PITCH_TOTAL_DURATION_MS / (PITCH_MAX_ANGLE - PITCH_MIN_ANGLE)


class NotEnoughMissilesError(Exception):
    pass


class Launcher:
    def __init__(self, device: ThunderDevice) -> None:
        self._device = device
        self._lock = asyncio.Lock()
        self._missiles = MISSILE_COUNT
        self._yaw = 0
        self._pitch = 0

    @property
    def state(self) -> dict:
        return {
            "connected": self._device.connected,
            "missiles": self._missiles,
            "yaw": self._yaw,
            "pitch": self._pitch,
        }

    def _send(self, cmd: int, extra: int = 0x00) -> None:
        self._device.send([0x02, cmd, extra, 0x00, 0x00, 0x00, 0x00, 0x00])

    async def move(self, direction: str, duration_ms: int) -> None:
        cmd_map = {
            "up": Cmd.UP,
            "down": Cmd.DOWN,
            "left": Cmd.LEFT,
            "right": Cmd.RIGHT,
        }
        cmd = cmd_map.get(direction)
        if cmd is None:
            raise ValueError(f"Unknown direction '{direction}'. Valid: up, down, left, right.")
        async with self._lock:
            self._send(cmd)
            await asyncio.sleep(duration_ms / 1000)
            self._send(Cmd.STOP)

    async def yaw(self, angle: int) -> None:
        angle = max(YAW_MIN_ANGLE, min(YAW_MAX_ANGLE, angle))
        delta = angle - self._yaw
        if delta == 0:
            return
        duration_ms = int(abs(delta) * _YAW_MS_PER_DEGREE)
        direction = "right" if delta > 0 else "left"
        await self.move(direction, duration_ms)
        self._yaw = angle

    async def pitch(self, angle: int) -> None:
        angle = max(PITCH_MIN_ANGLE, min(PITCH_MAX_ANGLE, angle))
        delta = angle - self._pitch
        if delta == 0:
            return
        duration_ms = int(abs(delta) * _PITCH_MS_PER_DEGREE)
        direction = "up" if delta > 0 else "down"
        await self.move(direction, duration_ms)
        self._pitch = angle

    async def fire(self, shots: int = 1) -> None:
        if shots < 1:
            raise ValueError("shots must be >= 1")
        if shots > self._missiles:
            raise NotEnoughMissilesError(
                f"Cannot fire {shots} shot(s): only {self._missiles} missile(s) remaining."
            )
        async with self._lock:
            for _ in range(shots):
                self._send(Cmd.FIRE)
                await asyncio.sleep(RELOAD_DELAY_MS / 1000)
                self._missiles -= 1

    async def park(self) -> None:
        async with self._lock:
            self._send(Cmd.LEFT)
            await asyncio.sleep(YAW_TOTAL_DURATION_MS / 1000)
            self._send(Cmd.DOWN)
            await asyncio.sleep(PITCH_TOTAL_DURATION_MS / 1000)
            self._send(Cmd.STOP)
        self._yaw = YAW_MIN_ANGLE
        self._pitch = PITCH_MIN_ANGLE

    def led(self, on: bool) -> None:
        self._send(Cmd.LED, Led.ON if on else Led.OFF)

    def reload(self) -> None:
        self._missiles = MISSILE_COUNT
