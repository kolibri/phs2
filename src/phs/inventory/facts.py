import json
from typing import Protocol

from pydantic import BaseModel, Field

from phs.execution.target import Target


class OsFacts(BaseModel):
    id: str
    version: str


class BlkidFacts(BaseModel):
    device: str
    mountpoint: str
    uuid: str | None = None
    label: str | None = None
    type: str | None = None
    partuuid: str | None = None
    properties: dict[str, str] = Field(default_factory=dict)


class Facts(BaseModel):
    os: OsFacts
    blkid: dict[str, BlkidFacts] = Field(default_factory=dict)


class FactCollector(Protocol):
    def collect(self, target: Target) -> object: ...


class OsFactCollector:
    def collect(self, target: Target) -> OsFacts:
        result = target.run("cat -- /etc/os-release")
        if result.returncode != 0:
            raise RuntimeError(
                f"Could not read /etc/os-release: {result.stderr.strip()}"
            )

        values: dict[str, str] = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.partition("=")
            if not separator:
                continue

            values[key] = value.strip().strip('"')

        try:
            os_id = values["ID"]
        except KeyError:
            raise RuntimeError("/etc/os-release does not contain ID") from None

        version = values.get("VERSION_ID") or values.get("BUILD_ID") or "unknown"
        return OsFacts(id=os_id, version=version)


class BlkidFactCollector:
    def collect(self, target: Target) -> dict[str, BlkidFacts]:
        blkid = target.run("blkid -o export")
        if blkid.returncode != 0:
            raise RuntimeError(f"Could not run blkid: {blkid.stderr.strip()}")

        records = _parse_blkid_export(blkid.stdout)

        mounts = target.run("findmnt -J -o SOURCE,TARGET")
        if mounts.returncode != 0:
            raise RuntimeError(f"Could not run findmnt: {mounts.stderr.strip()}")

        return _mount_blkid_records(records, mounts.stdout)


def collect_facts(target: Target) -> Facts:
    os_facts = OsFactCollector().collect(target)
    blkid_facts = BlkidFactCollector().collect(target)
    return Facts(os=os_facts, blkid=blkid_facts)


def _parse_blkid_export(output: str) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    current: dict[str, str] = {}

    for line in output.splitlines():
        if not line:
            _store_blkid_record(records, current)
            current = {}
            continue

        key, separator, value = line.partition("=")
        if separator:
            current[key] = value

    _store_blkid_record(records, current)
    return records


def _store_blkid_record(
    records: dict[str, dict[str, str]],
    record: dict[str, str],
) -> None:
    device = record.get("DEVNAME")
    if device:
        records[device] = dict(record)


def _mount_blkid_records(
    records: dict[str, dict[str, str]],
    output: str,
) -> dict[str, BlkidFacts]:
    data = json.loads(output)
    mounted: dict[str, BlkidFacts] = {}

    for filesystem in data.get("filesystems", []):
        source = filesystem.get("source")
        mountpoint = filesystem.get("target")
        if not source or not mountpoint:
            continue

        record = records.get(source)
        if record is None and source.startswith("UUID="):
            uuid = source.removeprefix("UUID=")
            record = next(
                (
                    candidate
                    for candidate in records.values()
                    if candidate.get("UUID") == uuid
                ),
                None,
            )

        if record is None:
            continue

        mounted[mountpoint] = BlkidFacts(
            device=record["DEVNAME"],
            mountpoint=mountpoint,
            uuid=record.get("UUID"),
            label=record.get("LABEL"),
            type=record.get("TYPE"),
            partuuid=record.get("PARTUUID"),
            properties=dict(record),
        )

    return mounted
