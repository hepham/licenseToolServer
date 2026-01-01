"""
Device Fingerprint Collection

Collects hardware identifiers to create a unique device fingerprint.
Handles edge cases gracefully with multiple fallback strategies.
"""

import hashlib
import platform
import subprocess
import re
import uuid
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class FingerprintError(Exception):
    """Raised when fingerprint collection fails critically."""
    pass


class DeviceFingerprint:
    """
    Collects and manages device hardware fingerprint data.
    
    Handles edge cases:
    - Missing/inaccessible hardware IDs
    - Virtual machines with generic IDs
    - Permission issues
    - Different OS versions
    
    Uses multiple fallback strategies to ensure a unique fingerprint.
    """

    # Generic values to reject
    INVALID_VALUES = {
        "",
        "none",
        "n/a",
        "default",
        "unknown",
        "to be filled by o.e.m.",
        "not available",
        "system serial number",
        "system manufacturer",
        "0",
        "123456789",
    }

    def __init__(self, strict: bool = False):
        """
        Initialize fingerprint collector.
        
        Args:
            strict: If True, raise FingerprintError when hardware IDs unavailable.
                   If False, use fallback values (default).
        """
        self._strict = strict
        self._cpu_id: Optional[str] = None
        self._disk_serial: Optional[str] = None
        self._motherboard_id: Optional[str] = None
        self._mac_address: Optional[str] = None
        self._device_id: Optional[str] = None
        self._fallback_count = 0

    @property
    def cpu_id(self) -> str:
        """Get the CPU identifier."""
        if self._cpu_id is None:
            self._cpu_id = self._get_cpu_id()
        return self._cpu_id

    @property
    def disk_serial(self) -> str:
        """Get the primary disk serial number."""
        if self._disk_serial is None:
            self._disk_serial = self._get_disk_serial()
        return self._disk_serial

    @property
    def motherboard_id(self) -> str:
        """Get the motherboard serial number."""
        if self._motherboard_id is None:
            self._motherboard_id = self._get_motherboard_id()
        return self._motherboard_id

    @property
    def mac_address(self) -> str:
        """Get the primary MAC address."""
        if self._mac_address is None:
            self._mac_address = self._get_mac_address()
        return self._mac_address

    @property
    def device_id(self) -> str:
        """
        Get the unique device identifier.
        
        This is a SHA-256 hash of all hardware identifiers combined.
        """
        if self._device_id is None:
            combined = f"{self.cpu_id}:{self.disk_serial}:{self.motherboard_id}:{self.mac_address}"
            self._device_id = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        return self._device_id

    @property
    def fallback_count(self) -> int:
        """Number of hardware IDs that used fallback values."""
        _ = self.device_id  # Ensure all values are collected
        return self._fallback_count

    @property
    def is_reliable(self) -> bool:
        """True if at least 2 hardware IDs were successfully retrieved."""
        return self.fallback_count <= 2

    def to_dict(self) -> dict:
        """Return all fingerprint data as a dictionary."""
        return {
            "cpu_id": self.cpu_id,
            "disk_serial": self.disk_serial,
            "motherboard_id": self.motherboard_id,
            "mac_address": self.mac_address,
        }

    def _is_valid(self, value: Optional[str]) -> bool:
        """Check if a hardware ID value is valid (not generic/empty)."""
        if not value:
            return False
        return value.lower().strip() not in self.INVALID_VALUES

    def _run_command(self, cmd: List[str], timeout: int = 5) -> Optional[str]:
        """Safely run a command and return output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            logger.debug(f"Command {cmd} failed: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error running {cmd}: {e}")
        return None

    def _get_fallback(self, prefix: str) -> str:
        """Generate a fallback identifier."""
        self._fallback_count += 1
        # Use multiple sources for fallback uniqueness
        node = platform.node() or "unknown"
        machine = platform.machine() or "unknown"
        fallback = f"{prefix}-{node}-{machine}-{os.getpid()}"
        
        if self._strict:
            raise FingerprintError(f"Could not retrieve {prefix}, fallback: {fallback}")
        
        logger.warning(f"Using fallback for {prefix}: {fallback}")
        return fallback

    def _get_cpu_id(self) -> str:
        """Retrieve the CPU identifier with multiple fallback strategies."""
        system = platform.system()
        strategies = []

        if system == "Windows":
            strategies = [
                lambda: self._windows_wmic("cpu", "ProcessorId"),
                lambda: self._windows_wmic("cpu", "Name"),
                lambda: self._run_command(["powershell", "-Command", 
                    "(Get-CimInstance -ClassName Win32_Processor).ProcessorId"]),
            ]
        elif system == "Linux":
            strategies = [
                lambda: self._linux_read_file("/sys/class/dmi/id/product_uuid"),
                lambda: self._linux_cpuinfo_field("Serial"),
                lambda: self._linux_cpuinfo_field("model name"),
                lambda: self._run_command(["dmidecode", "-s", "processor-version"]),
            ]
        elif system == "Darwin":
            strategies = [
                lambda: self._run_command(["sysctl", "-n", "machdep.cpu.brand_string"]),
                lambda: self._run_command(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]),
            ]

        for strategy in strategies:
            try:
                value = strategy()
                if self._is_valid(value):
                    # Hash long values for consistency
                    if len(value) > 64:
                        return hashlib.md5(value.encode()).hexdigest()
                    return value
            except Exception as e:
                logger.debug(f"CPU strategy failed: {e}")
                continue

        return self._get_fallback("cpu")

    def _get_disk_serial(self) -> str:
        """Retrieve the primary disk serial number."""
        system = platform.system()
        strategies = []

        if system == "Windows":
            strategies = [
                lambda: self._windows_wmic("diskdrive", "SerialNumber"),
                lambda: self._windows_wmic("logicaldisk", "VolumeSerialNumber"),
                lambda: self._run_command(["powershell", "-Command",
                    "(Get-PhysicalDisk | Select-Object -First 1).SerialNumber"]),
            ]
        elif system == "Linux":
            strategies = [
                lambda: self._run_command(["lsblk", "-o", "SERIAL", "-dn"]),
                lambda: self._linux_read_file("/sys/block/sda/device/serial"),
                lambda: self._linux_read_file("/sys/block/nvme0n1/serial"),
                lambda: self._run_command(["udevadm", "info", "--query=property", 
                    "--name=/dev/sda"]),
            ]
        elif system == "Darwin":
            strategies = [
                self._darwin_disk_serial,
                lambda: self._run_command(["diskutil", "info", "disk0"]),
            ]

        for strategy in strategies:
            try:
                value = strategy()
                if self._is_valid(value):
                    # Clean up and return first valid serial
                    clean = value.split('\n')[0].strip()
                    if self._is_valid(clean):
                        return clean
            except Exception as e:
                logger.debug(f"Disk strategy failed: {e}")
                continue

        return self._get_fallback("disk")

    def _get_motherboard_id(self) -> str:
        """Retrieve the motherboard serial number."""
        system = platform.system()
        strategies = []

        if system == "Windows":
            strategies = [
                lambda: self._windows_wmic("baseboard", "SerialNumber"),
                lambda: self._windows_wmic("baseboard", "Product"),
                lambda: self._windows_wmic("csproduct", "UUID"),
            ]
        elif system == "Linux":
            strategies = [
                lambda: self._linux_read_file("/sys/class/dmi/id/board_serial"),
                lambda: self._linux_read_file("/sys/class/dmi/id/product_uuid"),
                lambda: self._linux_read_file("/sys/class/dmi/id/board_name"),
                lambda: self._run_command(["dmidecode", "-s", "baseboard-serial-number"]),
            ]
        elif system == "Darwin":
            strategies = [
                self._darwin_serial_number,
                lambda: self._run_command(["system_profiler", "SPHardwareDataType"]),
            ]

        for strategy in strategies:
            try:
                value = strategy()
                if self._is_valid(value):
                    return value
            except Exception as e:
                logger.debug(f"Motherboard strategy failed: {e}")
                continue

        return self._get_fallback("mb")

    def _get_mac_address(self) -> str:
        """Retrieve the primary network MAC address."""
        strategies = [
            self._mac_from_uuid,
            self._mac_from_getmac,
            self._mac_from_ifconfig,
        ]

        for strategy in strategies:
            try:
                value = strategy()
                if self._is_valid(value) and value != "00:00:00:00:00:00":
                    return value
            except Exception as e:
                logger.debug(f"MAC strategy failed: {e}")
                continue

        return self._get_fallback("mac")

    # --- Windows helpers ---
    
    def _windows_wmic(self, category: str, field: str) -> Optional[str]:
        """Run WMIC command on Windows."""
        output = self._run_command(["wmic", category, "get", field])
        if output:
            lines = output.strip().split('\n')
            if len(lines) >= 2:
                value = lines[1].strip()
                if self._is_valid(value):
                    return value
        return None

    # --- Linux helpers ---
    
    def _linux_read_file(self, path: str) -> Optional[str]:
        """Read a system file on Linux."""
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return None

    def _linux_cpuinfo_field(self, field: str) -> Optional[str]:
        """Extract a field from /proc/cpuinfo."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if field.lower() in line.lower():
                        return line.split(":")[-1].strip()
        except FileNotFoundError:
            pass
        return None

    # --- macOS helpers ---
    
    def _darwin_serial_number(self) -> Optional[str]:
        """Get macOS serial number."""
        output = self._run_command(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
        if output:
            match = re.search(r'"IOPlatformSerialNumber"\s*=\s*"(\S+)"', output)
            if match:
                return match.group(1)
        return None

    def _darwin_disk_serial(self) -> Optional[str]:
        """Get macOS disk serial."""
        output = self._run_command(["system_profiler", "SPSerialATADataType"])
        if output:
            match = re.search(r"Serial Number:\s*(\S+)", output)
            if match:
                return match.group(1)
        return None

    # --- MAC address helpers ---
    
    def _mac_from_uuid(self) -> Optional[str]:
        """Get MAC using uuid module."""
        mac = uuid.getnode()
        # Check if it's a real MAC (not randomly generated)
        if (mac >> 40) % 2 == 0:
            return ':'.join(format((mac >> i) & 0xff, '02x') for i in range(40, -1, -8))
        return None

    def _mac_from_getmac(self) -> Optional[str]:
        """Get MAC using getmac command (Windows)."""
        output = self._run_command(["getmac", "/fo", "csv", "/nh"])
        if output:
            match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}', output)
            if match:
                return match.group(0).lower().replace('-', ':')
        return None

    def _mac_from_ifconfig(self) -> Optional[str]:
        """Get MAC using ifconfig/ip command (Linux/macOS)."""
        for cmd in [["ip", "link"], ["ifconfig", "-a"]]:
            output = self._run_command(cmd)
            if output:
                # Find first non-loopback MAC
                macs = re.findall(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', output)
                for mac in macs:
                    mac_clean = mac.lower().replace('-', ':')
                    if mac_clean != "00:00:00:00:00:00":
                        return mac_clean
        return None

    def __repr__(self) -> str:
        return f"DeviceFingerprint(device_id={self.device_id[:16]}..., reliable={self.is_reliable})"
