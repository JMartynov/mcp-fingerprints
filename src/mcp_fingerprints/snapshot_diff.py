from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp_fingerprints.models import ToolContractSignature


@dataclass
class DiscoveredServer:
    server_name: str
    client_name: str
    package_name: str | None = None
    version: str | None = None
    tools: list[ToolContractSignature] = field(default_factory=list)
    toolset_canonical_hash: str | None = None
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_name": self.server_name,
            "client_name": self.client_name,
            "package_name": self.package_name,
            "version": self.version,
            "tools": [t.to_dict() for t in self.tools],
            "toolset_canonical_hash": self.toolset_canonical_hash,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "url": self.url,
            "headers": self.headers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscoveredServer:
        tools = [ToolContractSignature.from_dict(t) for t in data.get("tools", [])]
        return cls(
            server_name=data["server_name"],
            client_name=data["client_name"],
            package_name=data.get("package_name"),
            version=data.get("version"),
            tools=tools,
            toolset_canonical_hash=data.get("toolset_canonical_hash"),
            command=data.get("command"),
            args=data.get("args", []),
            env=data.get("env", {}),
            url=data.get("url"),
            headers=data.get("headers", {}),
        )


@dataclass
class ServerDriftDetail:
    server_name: str
    client_name: str
    old_version: str | None
    new_version: str | None
    old_hash: str | None
    new_hash: str | None
    changes: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(
            self.old_version != self.new_version
            or self.old_hash != self.new_hash
            or self.changes
        )


@dataclass
class InventorySnapshot:
    snapshot_version: str = "1.0.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    host_identifier: str = "local"
    servers: list[DiscoveredServer] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_version": self.snapshot_version,
            "timestamp": self.timestamp,
            "host_identifier": self.host_identifier,
            "servers": [s.to_dict() for s in self.servers],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InventorySnapshot:
        servers = [DiscoveredServer.from_dict(s) for s in data.get("servers", [])]
        return cls(
            snapshot_version=data.get("snapshot_version", "1.0.0"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            host_identifier=data.get("host_identifier", "local"),
            servers=servers,
        )

    def save(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> InventorySnapshot:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def load_file(cls, path: str | Path) -> InventorySnapshot:
        return cls.load(path)


@dataclass
class DiffResult:
    added_servers: list[DiscoveredServer] = field(default_factory=list)
    removed_servers: list[DiscoveredServer] = field(default_factory=list)
    modified_servers: list[ServerDriftDetail] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added_servers or self.removed_servers or self.modified_servers)

    @property
    def schema_drift_count(self) -> int:
        return len(self.modified_servers)


class InventoryDiffer:
    @staticmethod
    def compare(baseline: InventorySnapshot, current: InventorySnapshot) -> DiffResult:
        baseline_servers = {(s.client_name, s.server_name): s for s in baseline.servers}
        current_servers = {(s.client_name, s.server_name): s for s in current.servers}

        added = []
        removed = []
        modified = []

        for key, s_curr in current_servers.items():
            if key not in baseline_servers:
                added.append(s_curr)
            else:
                s_base = baseline_servers[key]
                drift = InventoryDiffer._compare_server(s_base, s_curr)
                if drift.has_drift:
                    modified.append(drift)

        for key, s_base in baseline_servers.items():
            if key not in current_servers:
                removed.append(s_base)

        return DiffResult(
            added_servers=added,
            removed_servers=removed,
            modified_servers=modified,
        )

    @staticmethod
    def _compare_server(old: DiscoveredServer, new: DiscoveredServer) -> ServerDriftDetail:
        changes = []
        
        # Tools comparison
        old_tools = {t.name: t for t in old.tools}
        new_tools = {t.name: t for t in new.tools}

        for t_name, t_new in new_tools.items():
            if t_name not in old_tools:
                changes.append(f"Tool '{t_name}' added")
            else:
                t_old = old_tools[t_name]
                if t_old.canonical_hash != t_new.canonical_hash:
                    # Deep comparison
                    if t_old.description != t_new.description:
                        changes.append(f"Tool '{t_name}': Description changed")
                    
                    old_props = set(t_old.property_keys)
                    new_props = set(t_new.property_keys)
                    
                    for prop in new_props - old_props:
                        prop_type = t_new.parameter_types.get(prop, 'unknown')
                        req = 'required' if prop in t_new.required_keys else 'optional'
                        changes.append(f"Tool '{t_name}': Parameter '{prop}' added (type: {prop_type}, {req})")
                    for prop in old_props - new_props:
                        changes.append(f"Tool '{t_name}': Parameter '{prop}' removed")

                    # Param type changes
                    for prop in new_props.intersection(old_props):
                        if t_old.parameter_types.get(prop) != t_new.parameter_types.get(prop):
                            changes.append(f"Tool '{t_name}': Parameter '{prop}' type changed from {t_old.parameter_types.get(prop)} to {t_new.parameter_types.get(prop)}")
                        
                        old_req = prop in t_old.required_keys
                        new_req = prop in t_new.required_keys
                        if old_req != new_req:
                            changes.append(f"Tool '{t_name}': Parameter '{prop}' required status changed from {old_req} to {new_req}")

        for t_name in old_tools:
            if t_name not in new_tools:
                changes.append(f"Tool '{t_name}' removed")

        return ServerDriftDetail(
            server_name=new.server_name,
            client_name=new.client_name,
            old_version=old.version,
            new_version=new.version,
            old_hash=old.toolset_canonical_hash,
            new_hash=new.toolset_canonical_hash,
            changes=changes,
        )


def compare_snapshots(baseline: InventorySnapshot, current: InventorySnapshot) -> DiffResult:
    return InventoryDiffer.compare(baseline, current)

def save_inventory_snapshot(inventory: InventorySnapshot, path: str | Path) -> None:
    inventory.save(path)
