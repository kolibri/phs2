from __future__ import annotations

import ipaddress
import json
import os
import socket
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# ============================================================================
# Value objects
# ============================================================================


DiskInterface = Literal["virtio", "ide", "scsi", "nvme"]


@dataclass(frozen=True)
class DiskConfig:
    path: Path
    size_gb: int
    format: str = "qcow2"
    interface: DiskInterface = "nvme"

    def create(self, recreate: bool = False) -> None:
        if self.path.exists():
            if not recreate:
                return
            self.path.unlink()

        self.path.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "qemu-img",
                "create",
                "-f",
                self.format,
                str(self.path),
                f"{self.size_gb}G",
            ],
            check=True,
        )

    def qemu_args(self, disk_id: str = "disk0") -> list[str]:
        if self.interface == "nvme":
            return [
                "-drive",
                (f"if=none,id={disk_id},format={self.format},file={self.path}"),
                "-device",
                f"nvme,drive={disk_id},serial={disk_id}",
            ]

        return [
            "-drive",
            (f"file={self.path},format={self.format},if={self.interface}"),
        ]


@dataclass(frozen=True)
class SshInfo:
    host: str
    port: int
    user: str
    private_key: Path | None = None

    def command(self, *args: str) -> list[str]:
        command = [
            "ssh",
            "-p",
            str(self.port),
        ]

        if self.private_key is not None:
            command += [
                "-i",
                str(self.private_key),
            ]

        command += [
            f"{self.user}@{self.host}",
            *args,
        ]

        return command


@dataclass(frozen=True)
class NetworkConfig:
    name: str
    address: ipaddress.IPv4Network  # is the subnet used by the virtual network.
    guest_address: ipaddress.IPv4Address  # is the address of the VM inside that subnet.
    ssh_host_port: int | None = None  # is the host-side port forwarded to guest TCP/22.

    def __init__(
        self,
        name: str,
        address: str,
        guest_address: str,
        ssh_host_port: int | None = None,
    ):
        address = ipaddress.ip_network(address)
        if not isinstance(address, ipaddress.IPv4Network):
            raise TypeError("Only IPv4 networks are supported")

        guest_address = ipaddress.ip_address(guest_address)
        if not isinstance(guest_address, ipaddress.IPv4Address):
            raise TypeError("Only IPv4 networks are supported")

        if guest_address not in address:
            raise ValueError(f"{guest_address} is not inside {address}")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "address", address)
        object.__setattr__(self, "guest_address", guest_address)
        object.__setattr__(self, "ssh_host_port", ssh_host_port)

    def qemu_args(self) -> list[str]:
        netdev = (
            f"user,id={self.name},net={self.address},dhcpstart={self.guest_address}"
        )

        if self.ssh_host_port is not None:
            netdev += f",hostfwd=tcp:127.0.0.1:{self.ssh_host_port}-:22"

        return [
            "-netdev",
            netdev,
            "-device",
            f"virtio-net-pci,netdev={self.name}",
        ]


@dataclass(frozen=True)
class BootMedia:
    iso_images: tuple[Path, ...] = ()

    def qemu_args(self) -> list[str]:
        args: list[str] = []

        for iso in self.iso_images:
            args += [
                "-drive",
                (f"file={iso},media=cdrom,readonly=on"),
            ]

        return args


@dataclass(frozen=True)
class VmConfig:
    name: str
    memory_mb: int = 2048
    cpus: int = 2
    disks: tuple[DiskConfig, ...] = ()
    networks: tuple[NetworkConfig, ...] = ()
    ssh: SshInfo | None = None
    qemu_binary: str = "qemu-system-x86_64"
    runtime_dir: Path = Path(".qemu")
    extra_args: tuple[str, ...] = ()
    qmp_socket: Path | None = None

    def pid_file(self) -> Path:
        return self.runtime_dir / f"{self.name}.pid"

    def log_file(self) -> Path:
        return self.runtime_dir / f"{self.name}.log"

    def monitor_socket(self) -> Path:
        if self.qmp_socket is not None:
            return self.qmp_socket

        return self.runtime_dir / f"{self.name}.qmp"


class QmpError(RuntimeError):
    pass


class QmpMonitor:
    def __init__(
        self,
        socket_path: Path,
        timeout: float = 5.0,
    ):
        self.socket_path = socket_path
        self.timeout = timeout

    def command(
        self,
        execute: str,
        arguments: dict | None = None,
    ) -> dict:
        with socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        ) as sock:
            sock.settimeout(self.timeout)
            sock.connect(str(self.socket_path))
            greeting = self._read_message(sock)

            if "QMP" not in greeting:
                raise QmpError(f"Invalid QMP greeting: {greeting!r}")

            self._send(sock, {"execute": "qmp_capabilities"})
            capabilities_response = self._read_message(sock)

            if "error" in capabilities_response:
                raise QmpError(f"Failed to initialize QMP: {capabilities_response!r}")

            request: dict = {"execute": execute}

            if arguments:
                request["arguments"] = arguments

            self._send(sock, request)
            response = self._read_message(sock)

            if "error" in response:
                raise QmpError(f"QMP command {execute!r} failed: {response!r}")

            return response

    def shutdown(self) -> None:
        self.command("system_powerdown")

    def quit(self) -> None:
        self.command("quit")

    def _send(
        self,
        sock: socket.socket,
        message: dict,
    ) -> None:
        sock.sendall(json.dumps(message).encode("utf-8") + b"\r\n")

    def _read_message(
        self,
        sock: socket.socket,
    ) -> dict:
        data = b""
        while b"\r\n" not in data:
            chunk = sock.recv(4096)
            if not chunk:
                raise QmpError("QMP connection closed unexpectedly")
            data += chunk
        line, _, _ = data.partition(b"\r\n")
        return json.loads(line.decode("utf-8"))


@dataclass(frozen=True)
class CloudImage:
    path: Path
    meta_data: Path = Path(__file__).parent / "files/meta-data"
    user_data: Path = Path(__file__).parent / "files/user-data"

    def create(self, recreate: bool = False):
        if self.path.exists():
            if not recreate:
                return
            self.path.unlink()

        if not self.meta_data.exists():
            raise ValueError(
                f"file for metadata '{self.meta_data.absolute()!s}' does not exist"
            )
        if not self.user_data.exists():
            raise ValueError(
                f"file for userdata '{self.user_data.absolute()!s}' does not exist"
            )

        subprocess.run(
            [
                "xorriso",
                "-as",
                "genisoimage",
                "-output",
                str(self.path),
                "-volid",
                "CIDATA",
                "-joliet",
                "-rock",
                str(self.user_data),
                str(self.meta_data),
            ],
            check=True,
        )


class QemuVm:
    def __init__(self, config: VmConfig):
        self.config = config
        self._process: subprocess.Popen | None = None

    def boot(
        self, *iso_images: Path, gui: bool = False, recreate_disks: bool = False
    ) -> None:
        if self._is_running():
            raise RuntimeError(f"VM {self.config.name!r} is already running")

        for disk in self.config.disks:
            disk.create(recreate_disks)

        self._prepare_runtime_directory()
        self._remove_stale_runtime_files()

        command = self._build_command(BootMedia(tuple(iso_images)), gui)
        log_file = self.config.log_file()
        # log = open(log_file, "ab")

        with open(log_file, "ab") as log:
            try:
                self._process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            except Exception:
                log.close()
                raise

            self.config.pid_file().write_text(str(self._process.pid))
            self._wait_for_qmp()

    def shutdown(
        self,
        timeout: float = 30,
    ) -> None:
        if not self._is_running():
            self._cleanup_runtime_files()
            return

        monitor = QmpMonitor(self.config.monitor_socket())

        try:
            monitor.shutdown()
        except OSError, QmpError:
            pass

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if not self._is_running():
                self._cleanup_runtime_files()
                return
            time.sleep(0.25)

        self._force_shutdown()

    def _is_running(self) -> bool:
        if self._process is not None:
            return self._process.poll() is None

        pid_file = self.config.pid_file()

        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text())
        except ValueError:
            return False

        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

        return True

    def ssh_info(self) -> SshInfo:
        if self.config.ssh is None:
            raise RuntimeError(f"VM {self.config.name!r} has no SSH configuration")

        return self.config.ssh

    def _build_command(self, boot_media: BootMedia, gui: bool) -> list[str]:
        args = [
            self.config.qemu_binary,
            "-name",
            self.config.name,
            "-m",
            str(self.config.memory_mb),
            "-smp",
            str(self.config.cpus),
            # KVM acceleration.
            "-enable-kvm",
            # QMP UNIX socket.
            "-qmp",
            f"unix:{self.config.monitor_socket()},server=on,wait=off",
            # PID file.
            "-pidfile",
            str(self.config.pid_file()),
        ]

        if gui:
            args += [
                "-display",
                "gtk",
            ]
        else:
            args += [
                "-display",
                "none",
                "-serial",
                "mon:stdio",
            ]

        for index, disk in enumerate(self.config.disks):
            args.extend(disk.qemu_args(f"disk{index}"))
        for network in self.config.networks:
            args.extend(network.qemu_args())
        args.extend(boot_media.qemu_args())
        args.extend(self.config.extra_args)

        return args

    def _wait_for_qmp(
        self,
        timeout: float = 10,
    ) -> None:
        deadline = time.monotonic() + timeout
        socket_path = self.config.monitor_socket()

        while time.monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                raise RuntimeError(
                    f"QEMU exited while starting VM "
                    f"{self.config.name!r}. "
                    f"See {self.config.log_file()}"
                )

            if socket_path.exists():
                try:
                    monitor = QmpMonitor(socket_path)
                    monitor.command("query-status")
                    return
                except (
                    OSError,
                    QmpError,
                    ConnectionError,
                ):
                    pass

            time.sleep(0.1)

        raise TimeoutError(f"QMP did not become available for VM {self.config.name!r}")

    def _force_shutdown(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()

            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

        self._cleanup_runtime_files()

    def _prepare_runtime_directory(self) -> None:
        self.config.runtime_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _remove_stale_runtime_files(self) -> None:
        self.config.pid_file().unlink(missing_ok=True)

        self.config.monitor_socket().unlink(missing_ok=True)

    def _cleanup_runtime_files(self) -> None:
        self.config.pid_file().unlink(missing_ok=True)

        self.config.monitor_socket().unlink(missing_ok=True)


# ============================================================================
# VM manager
# ============================================================================


class QemuVmManager:
    """
    Convenience wrapper for a group of VMs.

    Useful for integration tests where several machines form a topology.
    """

    def __init__(
        self,
        vms: Sequence[QemuVm],
    ):
        self._vms = {vm.config.name: vm for vm in vms}

    def get(self, name: str) -> QemuVm:
        return self._vms[name]

    def boot_all(self) -> None:
        for vm in self._vms.values():
            vm.boot()

    def shutdown_all(self) -> None:
        for vm in self._vms.values():
            vm.shutdown()

    def __getitem__(self, name: str) -> QemuVm:
        return self._vms[name]

    def __iter__(self):
        return iter(self._vms.values())
