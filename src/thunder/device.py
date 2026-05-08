import usb.core
import usb.util

from .constants import VENDOR_ID, PRODUCT_ID


class DeviceNotFoundError(Exception):
    pass


class ThunderDevice:
    _CTRL_REQUEST_TYPE = 0x21
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
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except (NotImplementedError, usb.core.USBError):
            pass
        dev.set_configuration()
        self._dev = dev

    def disconnect(self) -> None:
        if self._dev is not None:
            usb.util.dispose_resources(self._dev)
            self._dev = None

    @property
    def connected(self) -> bool:
        return self._dev is not None

    def send(self, payload: list[int]) -> None:
        if self._dev is None:
            raise RuntimeError("Device not connected")
        self._dev.ctrl_transfer(
            self._CTRL_REQUEST_TYPE,
            self._CTRL_REQUEST,
            0, 0,
            payload,
        )
