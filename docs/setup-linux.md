# Setup: Linux

## Prerequisites

- Docker and Docker Compose
- The launcher plugged into a USB port

## Installation

**1. Install the udev rule** (one-time):

```bash
sudo cp udev/99-dream-cheeky.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

This allows Docker to access the USB device without running as root. Without it, the container will get `USBError: [Errno 13] Access denied`.

**2. Start the server:**

```bash
docker compose up
```

The web UI is available at `http://localhost:8000` and the API at `http://localhost:8000/status`.

---

## Troubleshooting

**Device not found**

Verify the launcher is visible to the OS:

```bash
lsusb | grep 2123
```

If it does not appear, try a different USB port or cable. If `lsusb` is not available, install `usbutils`:

```bash
sudo apt install usbutils
```

**Permission denied (`USBError: [Errno 13]`)**

The udev rule may not have been applied yet, or was applied before the device was plugged in:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
# Then unplug and replug the launcher
```

**Container sees the device but returns 503**

Verify the container can open the device:

```bash
docker compose exec thunder python -c "import usb.core; print(usb.core.find(idVendor=0x2123, idProduct=0x1010))"
```

If this prints `None`, the udev rule is not applied or the device is not mounted in the container. Check that `compose.yaml` has the `devices` entry:

```yaml
devices:
  - /dev/bus/usb:/dev/bus/usb
```
