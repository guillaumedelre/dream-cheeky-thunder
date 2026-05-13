"""High-level launcher control.

Translates human-friendly commands (yaw to 45°, fire 2 shots) into
timed USB command sequences and tracks the estimated device state.

Position tracking is time-based and therefore approximate. Call park()
to reset to a known physical position before any precision targeting.
"""

import asyncio

from pydantic import BaseModel

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

# Derived from full-sweep calibration: how many milliseconds per degree of rotation.
_YAW_MS_PER_DEGREE = YAW_TOTAL_DURATION_MS / (YAW_MAX_ANGLE - YAW_MIN_ANGLE)
_PITCH_MS_PER_DEGREE = PITCH_TOTAL_DURATION_MS / (PITCH_MAX_ANGLE - PITCH_MIN_ANGLE)


class LauncherState(BaseModel):
    connected: bool
    missiles: int
    yaw: int
    pitch: int
    led: bool


class NotEnoughMissilesError(Exception):
    pass


class Launcher:
    def __init__(self, device: ThunderDevice) -> None:
        self._device = device
        # Prevents concurrent HTTP requests from sending overlapping USB commands,
        # which would corrupt the motor state (e.g. two moves running simultaneously).
        self._lock = asyncio.Lock()
        self._missiles = MISSILE_COUNT
        # Assumed starting position; call park() to synchronize with physical reality.
        self._yaw = 0
        self._pitch = 0
        self._led = False

    @property
    def state(self) -> LauncherState:
        """Returns the current estimated device state."""
        return LauncherState(
            connected=self._device.connected,
            missiles=self._missiles,
            yaw=self._yaw,
            pitch=self._pitch,
            led=self._led,
        )

    async def _send(self, cmd: int, extra: int = 0x00) -> None:
        # The device protocol requires an 8-byte payload.
        # Byte 0 is always 0x02 (fixed protocol header).
        # Byte 1 is the command. Byte 2 is an optional parameter (used for LED state).
        # Bytes 3-7 are always zero.
        await asyncio.to_thread(self._device.send, [0x02, cmd, extra, 0x00, 0x00, 0x00, 0x00, 0x00])

    async def move(self, direction: str, duration_ms: int) -> None:
        """Move in a raw direction for a fixed duration, then stop."""
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
            await self._send(cmd)
            # Hold the motor running for the requested duration, then send STOP.
            await asyncio.sleep(duration_ms / 1000)
            await self._send(Cmd.STOP)

    async def yaw(self, angle: int) -> None:
        """Rotate horizontally to a target angle relative to the current estimated position."""
        angle = max(YAW_MIN_ANGLE, min(YAW_MAX_ANGLE, angle))
        async with self._lock:
            delta = angle - self._yaw
            if delta == 0:
                return
            duration_ms = int(abs(delta) * _YAW_MS_PER_DEGREE)
            await self._send(Cmd.RIGHT if delta > 0 else Cmd.LEFT)
            await asyncio.sleep(duration_ms / 1000)
            await self._send(Cmd.STOP)
            self._yaw = angle

    async def pitch(self, angle: int) -> None:
        """Tilt vertically to a target angle relative to the current estimated position."""
        angle = max(PITCH_MIN_ANGLE, min(PITCH_MAX_ANGLE, angle))
        async with self._lock:
            delta = angle - self._pitch
            if delta == 0:
                return
            duration_ms = int(abs(delta) * _PITCH_MS_PER_DEGREE)
            await self._send(Cmd.UP if delta > 0 else Cmd.DOWN)
            await asyncio.sleep(duration_ms / 1000)
            await self._send(Cmd.STOP)
            self._pitch = angle

    async def fire(self, shots: int = 1) -> None:
        """Fire N shots sequentially, waiting for the reload cycle between each."""
        if shots < 1:
            raise ValueError("shots must be >= 1")
        if shots > self._missiles:
            raise NotEnoughMissilesError(
                f"Cannot fire {shots} shot(s): only {self._missiles} missile(s) remaining."
            )
        async with self._lock:
            for _ in range(shots):
                await self._send(Cmd.FIRE)
                # The launcher needs RELOAD_DELAY_MS to mechanically advance
                # to the next missile before it can accept another FIRE command.
                await asyncio.sleep(RELOAD_DELAY_MS / 1000)
                self._missiles -= 1

    async def park(self) -> None:
        """Drive to the mechanical hard stops (bottom-left) to establish a known position.

        This ignores the estimated position and holds the motors running against the
        physical limits for the full sweep duration, guaranteeing alignment regardless
        of where the launcher actually was.
        """
        async with self._lock:
            await self._send(Cmd.LEFT)
            await asyncio.sleep(YAW_TOTAL_DURATION_MS / 1000)
            await self._send(Cmd.DOWN)
            await asyncio.sleep(PITCH_TOTAL_DURATION_MS / 1000)
            await self._send(Cmd.STOP)
            # After hitting the hard stops, we are definitively at the minimum angles.
            self._yaw = YAW_MIN_ANGLE
            self._pitch = PITCH_MIN_ANGLE

    async def led(self, on: bool) -> None:
        """Toggle the blue LED ring on the launcher base."""
        # LED uses HID report ID 0x03, distinct from the movement report (0x02).
        payload = [0x03, Led.ON if on else Led.OFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        async with self._lock:
            await asyncio.to_thread(self._device.send, payload)
            self._led = on

    async def reload(self) -> None:
        """Reset the missile counter after manually reloading the launcher."""
        async with self._lock:
            self._missiles = MISSILE_COUNT
