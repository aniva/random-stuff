# Project: Waveshare ESP32-C6 Telemetry Module
**Document:** Firmware Extraction & Restoration Protocol (`backup_reflash.md`)
**Author:** Aniva
**Date:** May 14, 2026

## 1. Architectural Constraints & WSL Interoperability
Executing direct hardware flashing protocols within a Windows Subsystem for Linux (WSL) environment introduces two strict structural barriers that must be bypassed:

* **Hardware Isolation (COM Ports):** The WSL2 Linux kernel cannot natively communicate with Windows COM ports (e.g., `COM4`). Standard Linux `esptool` execution will fail to detect the target CH343 UART bridge.
* **OS Protection (PEP 668):** Modern Debian/Ubuntu distributions enforce an `externally-managed-environment` policy. Attempting to install `esptool` via the native Linux `python3 -m pip` command will trigger an operational block to protect core OS dependencies.

**Resolution Protocol:** The protocol utilizes WSL Interoperability to execute the Windows-native Python executable provisioned by PlatformIO (`.platformio/penv`). This bypasses PEP 668 entirely and forces the execution context back to the Windows host layer, restoring unmitigated access to `COM4` while remaining within the WSL bash terminal.

## 2. Environment Provisioning
Initialize the dedicated PlatformIO Windows Python environment and inject the `esptool` dependency. This step requires execution from the WSL bash prompt.

```bash
# Inject esptool into the isolated Windows PlatformIO environment
/mnt/c/Users/me/.platformio/penv/Scripts/python.exe -m pip install esptool
```

## 3. Factory Firmware Extraction (Backup)
This execution extracts a 4MB payload representing the factory operational state of the Waveshare ESP32-C6, including the bootloader, partition table, and default UI application.

* **Target Port:** `COM4`
* **Baud Rate:** `460800` (Escalated to reduce transmission time)
* **Read Sector Size:** `0x400000` (4MB / 4,194,304 bytes)

```bash
# Execute payload extraction to the current working directory
/mnt/c/Users/me/.platformio/penv/Scripts/python.exe -m esptool -p COM4 -b 460800 read-flash 0 0x400000 waveshare_factory_backup.bin
```
*Note: The command explicitly utilizes the modern `read-flash` syntax to bypass deprecation warnings associated with the legacy `read_flash` command.*

### 3.1. Hardware Detection Telemetry
Upon successful execution, the CH343 bridge will engage the auto-reset circuit and report the following hardware parameters:

* **Chip Type:** ESP32-C6FH8 (QFN32) (revision v0.2)
* **Embedded Flash:** 8MB (Note: Standard Waveshare firmware partition is 4MB)
* **Crystal Frequency:** 40MHz

## 4. Firmware Restoration (Reflash)
If the custom telemetry UI application causes boot-loops or severe operational failure, execute this protocol to purge the flash sectors and rewrite the validated factory payload.

```bash
# Erase target sectors and flash the factory backup image
/mnt/c/Users/me/.platformio/penv/Scripts/python.exe -m esptool -p COM4 -b 460800 write-flash 0 waveshare_factory_backup.bin
```

### 4.1. Validation Protocol
1.  The tool will parse the `waveshare_factory_backup.bin` payload (approximately 1028119 compressed bytes).
2.  Upon completion, a `Hash of data verified` confirmation will generate.
3.  A `Hard resetting via RTS pin...` command will execute, dropping the DTR/RTS lines and releasing the microcontroller from Download Mode.
4.  The display module will immediately reboot into the default Waveshare factory UI.