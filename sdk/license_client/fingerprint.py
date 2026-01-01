"""
Device Fingerprint Collection

Collects hardware identifiers to create a unique device fingerprint.
"""

import hashlib
import platform
import subprocess
import re
import uuid
from typing import Optional


class DeviceFingerprint:
    """
    Collects and manages device hardware fingerprint data.
    
    Gathers CPU ID, disk serial, motherboard ID, and MAC address
    to create a unique device identifier.
    """

    def __init__(self):
        self._cpu_id: Optional[str] = None
        self._disk_serial: Optional[str] = None
        self._motherboard_id: Optional[str] = None
        self._mac_address: Optional[str] = None
        self._device_id: Optional[str] = None

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

    def to_dict(self) -> dict:
        """
        Return all fingerprint data as a dictionary.
        
        Used for API requests to the license server.
        """
        return {
            "cpu_id": self.cpu_id,
            "disk_serial": self.disk_serial,
            "motherboard_id": self.motherboard_id,
            "mac_address": self.mac_address,
        }

    def _get_cpu_id(self) -> str:
        """Retrieve the CPU identifier based on OS."""
        system = platform.system()
        
        try:
            if system == "Windows":
                output = subprocess.check_output(
                    ["wmic", "cpu", "get", "ProcessorId"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                lines = output.strip().split('\n')
                if len(lines) >= 2:
                    return lines[1].strip()
            
            elif system == "Linux":
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if "Serial" in line or "model name" in line:
                                return line.split(":")[-1].strip()
                except FileNotFoundError:
                    pass
                output = subprocess.check_output(
                    ["cat", "/sys/class/dmi/id/product_uuid"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                return output.strip()
            
            elif system == "Darwin":
                output = subprocess.check_output(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                return hashlib.md5(output.strip().encode()).hexdigest()
        
        except Exception:
            pass
        
        return f"cpu-{platform.processor()}-{platform.machine()}"

    def _get_disk_serial(self) -> str:
        """Retrieve the primary disk serial number."""
        system = platform.system()
        
        try:
            if system == "Windows":
                output = subprocess.check_output(
                    ["wmic", "diskdrive", "get", "SerialNumber"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                lines = output.strip().split('\n')
                if len(lines) >= 2:
                    serial = lines[1].strip()
                    if serial:
                        return serial
            
            elif system == "Linux":
                output = subprocess.check_output(
                    ["lsblk", "-o", "SERIAL", "-dn"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                serial = output.strip().split('\n')[0]
                if serial:
                    return serial
            
            elif system == "Darwin":
                output = subprocess.check_output(
                    ["system_profiler", "SPSerialATADataType"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                match = re.search(r"Serial Number:\s*(\S+)", output)
                if match:
                    return match.group(1)
        
        except Exception:
            pass
        
        return f"disk-{platform.node()}"

    def _get_motherboard_id(self) -> str:
        """Retrieve the motherboard serial number."""
        system = platform.system()
        
        try:
            if system == "Windows":
                output = subprocess.check_output(
                    ["wmic", "baseboard", "get", "SerialNumber"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                lines = output.strip().split('\n')
                if len(lines) >= 2:
                    serial = lines[1].strip()
                    if serial and serial != "To be filled by O.E.M.":
                        return serial
            
            elif system == "Linux":
                try:
                    with open("/sys/class/dmi/id/board_serial", "r") as f:
                        serial = f.read().strip()
                        if serial:
                            return serial
                except (FileNotFoundError, PermissionError):
                    pass
                output = subprocess.check_output(
                    ["cat", "/sys/class/dmi/id/product_uuid"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                return output.strip()
            
            elif system == "Darwin":
                output = subprocess.check_output(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                match = re.search(r'"IOPlatformSerialNumber"\s*=\s*"(\S+)"', output)
                if match:
                    return match.group(1)
        
        except Exception:
            pass
        
        return f"mb-{platform.node()}"

    def _get_mac_address(self) -> str:
        """Retrieve the primary network MAC address."""
        try:
            mac = uuid.getnode()
            if (mac >> 40) % 2 == 0:
                mac_str = ':'.join(
                    format((mac >> i) & 0xff, '02x')
                    for i in range(40, -1, -8)
                )
                return mac_str
        except Exception:
            pass
        
        return f"mac-{platform.node()}"

    def __repr__(self) -> str:
        return f"DeviceFingerprint(device_id={self.device_id[:16]}...)"
