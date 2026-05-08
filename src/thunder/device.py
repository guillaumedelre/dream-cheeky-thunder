"""Low-level USB communication layer for the Dream Cheeky Thunder launcher.

This module is the only place that touches the USB bus directly.
Everything above it (Launcher, API) works with commands, not raw bytes.
"""

import usb.core
import usb.util

from .constants import VENDOR_ID, PRODUCT_ID


class DeviceNotFoundError(Exception):
    pass


class ThunderDevice:
    # bmRequestType = 0x21: host-to-device, HID class request, recipient = interface (USB spec)
    _CTRL_REQUEST_TYPE = 0x21
    # bRequest = 0x09: HID SET_REPORT (USB HID spec §7.2.1)
    _CTRL_REQUEST = 0x09

    def __init__(self) -> None:
        self._dev: usb.core.Device | None = None

    def connect(self) -> None:
        dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        if dev is None:
            raise DeviceNotFoundError(
                f"Dream Cheeky Thunder not found (VID={VENDOR_ID:#06x}, PID={PRODUCT_ID:#06x}). "
                "Check the USB connection."
            )

        try:
            # Linux automatically binds a kernel HID driver to the device;
            # we must release it before we can claim the interface ourselves.
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except (NotImplementedError, usb.core.USBError):
            # NotImplementedError is raised on Windows and macOS where kernel driver
            # detachment is not applicable — safe to ignore on those platforms.
            pass

        # Activates the first (and only) USB configuration; required before any transfer.
        dev.set_configuration()
        self._dev = dev

    def disconnect(self) -> None:
        if self._dev is not None:
            # Releases all claimed interfaces and returns the device to the OS.
            usb.util.dispose_resources(self._dev)
            self._dev = None

    @property
    def connected(self) -> bool:
        return self._dev is not None

    def send(self, payload: list[int]) -> None:
        """Send an 8-byte control transfer to the launcher."""
        if self._dev is None:
            raise RuntimeError("Device not connected")
        self._dev.ctrl_transfer(
            self._CTRL_REQUEST_TYPE,
            self._CTRL_REQUEST,
            0, 0,   # wValue and wIndex are unused by this device
            payload,
        )
