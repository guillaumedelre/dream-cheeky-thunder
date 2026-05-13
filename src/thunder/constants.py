from enum import IntEnum

# Hardware identifiers for the Dream Cheeky Thunder USB missile launcher.
# These values are fixed by the manufacturer and cannot be changed.
VENDOR_ID = 0x2123
PRODUCT_ID = 0x1010

# Yaw = horizontal rotation. Full sweep: -135° (leftmost) to +135° (rightmost).
# The launcher physically takes 6000 ms to travel the full 270° range.
YAW_MIN_ANGLE = -135
YAW_MAX_ANGLE = 135
YAW_TOTAL_DURATION_MS = 6000

# Pitch = vertical tilt. Full sweep: -5° (lowest) to +45° (highest).
# The launcher physically takes 1000 ms to travel the full 50° range.
PITCH_MIN_ANGLE = -5
PITCH_MAX_ANGLE = 45
PITCH_TOTAL_DURATION_MS = 1000

# The physical launcher holds 4 foam missiles.
# After firing, the device needs 4500 ms to cycle and be ready for the next shot.
MISSILE_COUNT = 4
RELOAD_DELAY_MS = 4500


class Cmd(IntEnum):
    """Raw command bytes sent in the USB control transfer payload (byte index 1)."""
    DOWN = 0x01
    UP = 0x02
    LEFT = 0x04
    RIGHT = 0x08
    FIRE = 0x10
    STOP = 0x20


class Led(IntEnum):
    """LED state values sent as the extra byte (byte index 2) in report 0x03."""
    OFF = 0x00
    ON = 0x01
