from pathlib import Path

from helper.vm import CloudImage, DiskConfig, NetworkConfig, QemuVm, SshInfo, VmConfig

"""
Example:

    nfs-server
        192.168.100.10
        SSH -> localhost:2201

    nfs-client
        192.168.100.20
        SSH -> localhost:2202

Both VMs are connected to the same QEMU user-mode network.
"""

network_client = NetworkConfig(
    "testnet-client",
    address="192.168.100.0/24",
    guest_address="192.168.100.20",
    ssh_host_port=2202,
)

client = QemuVm(
    VmConfig(
        name="test-client",
        memory_mb=2048,
        cpus=2,
        disks=(
            DiskConfig(
                path=Path(".qemu/test-client.qcow2"),
                size_gb=20,
            ),
        ),
        networks=(network_client,),
        ssh=SshInfo(
            host="127.0.0.1",
            port=2202,
            user="root",
            private_key=Path("test-key"),
        ),
    )
)

# client.shutdown()

cloudimage = CloudImage(path=Path().cwd() / ".qemu/cloudimage.iso")
cloudimage.create(True)

client.boot(Path().cwd() / "archlinux-x86_64.iso", cloudimage.path, gui=True)
