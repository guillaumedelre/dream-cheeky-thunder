# 🪟 Setup: Windows (Docker Desktop + WSL2)

Docker on WSL2 cannot access USB devices directly. The USB device must be forwarded from Windows into the WSL2 kernel using [usbipd-win][usbipd] before Docker can reach it.

## ⚙️ How it works

```
Physical USB device
       |
  Windows kernel
       |
  usbipd-win        <-- forwards the device to WSL2
       |
  WSL2 kernel       <-- sees it as /dev/bus/usb/...
       |
  Docker container  <-- reaches it via the devices mount in compose.yaml
```

## ✅ Prerequisites

- Docker Desktop with WSL2 backend
- The launcher plugged into a USB port

---

## 📦 Installation

**1. Install usbipd-win** (PowerShell):

```powershell
winget install usbipd
```

Or download the MSI from the [releases page][usbipd-releases].

**2. Identify the launcher** (PowerShell):

```powershell
usbipd list
```

Example output:

```
BUSID  VID:PID    DEVICE                        STATE
2-1    046d:c52b  USB Input Device              Not shared
20-2   2123:1010  Dream Cheeky Thunder          Not shared
20-4   8087:0026  Intel Wireless Bluetooth      Not shared
```

Look for `2123:1010` in the `VID:PID` column. Note the corresponding `BUSID` (here `20-2`).

**3. Attach to WSL2** (PowerShell):

```powershell
usbipd attach --wsl --busid 20-2
```

Replace `20-2` with the `BUSID` from step 2. The `STATE` column should switch to `Attached` after this command.

**4. Install the udev rule** (WSL2 terminal, one-time):

```bash
sudo cp udev/99-dream-cheeky.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Without this rule, the container will get `USBError: [Errno 13] Access denied` even if the device is visible.

**5. Verify WSL2 sees the device** (WSL2 terminal):

```bash
cat /sys/bus/usb/devices/*/idVendor | grep 2123
```

If `2123` appears, the device is ready. If not, re-run step 3.

**6. Start the server** (WSL2 terminal):

```bash
docker compose up
```

The web UI is available at `http://localhost:8000` and the API at `http://localhost:8000/status`.

---

## 🔁 Keeping the device attached across reboots

By default, `usbipd attach` must be re-run after every Windows reboot or USB reconnect.

**usbipd v4+ (recommended): policy rule**

```powershell
usbipd policy add --effect Allow --vid 2123 --pid 1010
```

Check your version with `usbipd --version`. With this rule in place, the device attaches automatically whenever WSL2 is running.

**usbipd v3: `--auto-attach`**

```powershell
usbipd attach --wsl --busid <BUSID> --auto-attach
```

This re-attaches on reconnect but still requires a manual run after a Windows reboot. A Windows scheduled task on startup can automate this.

---

## 🔧 Troubleshooting

**🔍 `usbipd` not found in PowerShell**

Install it with `winget install usbipd` and open a new terminal.

**🔍 Device not visible in WSL2**

```bash
cat /sys/bus/usb/devices/*/idVendor | grep 2123
```

If nothing appears, the device is not attached. Re-run step 3 from PowerShell. Make sure the launcher is plugged in before attaching.

**🔒 Permission denied in the container (`USBError: [Errno 13]`)**

The udev rule is missing or was applied before the device was plugged in:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
# Then unplug and replug the launcher, and re-run usbipd attach
```

**⚠️ Device visible in WSL2 but container returns 503**

Verify the container can open the device:

```bash
docker compose exec thunder python -c "import usb.core; print(usb.core.find(idVendor=0x2123, idProduct=0x1010))"
```

If this prints `None` while the WSL2 check above finds the device, the udev rule is not applied. If it raises an error, the `devices` mount in `compose.yaml` may be missing:

```yaml
devices:
  - /dev/bus/usb:/dev/bus/usb
```

[usbipd]: https://github.com/dorssel/usbipd-win
[usbipd-releases]: https://github.com/dorssel/usbipd-win/releases
