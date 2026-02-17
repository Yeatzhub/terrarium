#!/usr/bin/env python3
"""
System Snapshot Tool

Captures current system state (CPU, memory, disk, services) and saves to JSON.
Supports comparison between snapshots.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import psutil


class SystemSnapshot:
    """Represents a system state snapshot."""
    
    def __init__(self) -> None:
        self.timestamp: str = datetime.now().isoformat()
        self.cpu: dict[str, Any] = {}
        self.memory: dict[str, Any] = {}
        self.disk: dict[str, Any] = {}
        self.services: list[dict[str, Any]] = []
    
    def capture(self) -> None:
        """Capture current system state."""
        self._capture_cpu()
        self._capture_memory()
        self._capture_disk()
        self._capture_services()
    
    def _capture_cpu(self) -> None:
        """Capture CPU usage information."""
        try:
            self.cpu = {
                "percent": psutil.cpu_percent(interval=0.5),
                "count": psutil.cpu_count(),
                "counts": {
                    "physical": psutil.cpu_count(logical=False),
                    "logical": psutil.cpu_count(logical=True),
                },
                "freq": self._get_cpu_freq(),
            }
        except Exception as e:
            self.cpu = {"error": str(e)}
    
    def _get_cpu_freq(self) -> Optional[dict[str, float]]:
        """Get CPU frequency info safely."""
        try:
            freq = psutil.cpu_freq()
            if freq:
                return {
                    "current": freq.current,
                    "min": freq.min if freq.min else None,
                    "max": freq.max if freq.max else None,
                }
        except Exception:
            pass
        return None
    
    def _capture_memory(self) -> None:
        """Capture memory usage information."""
        try:
            vm = psutil.virtual_memory()
            sm = psutil.swap_memory()
            self.memory = {
                "virtual": {
                    "total": vm.total,
                    "available": vm.available,
                    "percent": vm.percent,
                    "used": vm.used,
                    "free": vm.free,
                },
                "swap": {
                    "total": sm.total,
                    "used": sm.used,
                    "free": sm.free,
                    "percent": sm.percent,
                },
            }
        except Exception as e:
            self.memory = {"error": str(e)}
    
    def _capture_disk(self) -> None:
        """Capture disk usage information."""
        self.disk = {"partitions": []}
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    self.disk["partitions"].append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "opts": part.opts,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    })
                except PermissionError:
                    # Skip partitions we can't access
                    self.disk["partitions"].append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "error": "Permission denied",
                    })
        except Exception as e:
            self.disk["error"] = str(e)
    
    def _capture_services(self) -> None:
        """Capture list of systemd services and their status."""
        if not self._is_systemd():
            self.services = [{"note": "Not a systemd-based system"}]
            return
        
        try:
            result = subprocess.run(
                ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                services = []
                for line in lines[1:-2]:  # Skip header and footer
                    parts = line.split()
                    if len(parts) >= 4:
                        service_name = parts[0]
                        status = parts[2]
                        services.append({
                            "name": service_name,
                            "status": status,
                        })
                self.services = services
            else:
                self.services = [{"error": f"systemctl returned {result.returncode}"}]
        except subprocess.TimeoutExpired:
            self.services = [{"error": "Timeout while fetching services"}]
        except FileNotFoundError:
            self.services = [{"error": "systemctl not found"}]
        except Exception as e:
            self.services = [{"error": str(e)}]
    
    def _is_systemd(self) -> bool:
        """Check if running on a systemd system."""
        return Path("/run/systemd/system").exists()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "timestamp": self.timestamp,
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "services": self.services,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert snapshot to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_file(cls, path: Path) -> "SystemSnapshot":
        """Load snapshot from JSON file."""
        snapshot = cls()
        with open(path, "r") as f:
            data = json.load(f)
        snapshot.timestamp = data.get("timestamp", "unknown")
        snapshot.cpu = data.get("cpu", {})
        snapshot.memory = data.get("memory", {})
        snapshot.disk = data.get("disk", {})
        snapshot.services = data.get("services", [])
        return snapshot


def format_bytes(size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def format_percent(value: float) -> str:
    """Format percentage with color coding."""
    if value >= 90:
        return f"{value:.1f}% (CRITICAL)"
    elif value >= 70:
        return f"{value:.1f}% (WARNING)"
    return f"{value:.1f}%"


def generate_filename() -> str:
    """Generate filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"system_snapshot_{timestamp}.json"


def compare_snapshots(snapshot1: SystemSnapshot, snapshot2: SystemSnapshot) -> str:
    """Compare two snapshots and return formatted diff."""
    lines = []
    lines.append("=" * 70)
    lines.append("SNAPSHOT COMPARISON")
    lines.append("=" * 70)
    
    lines.append(f"\nOld snapshot: {snapshot1.timestamp}")
    lines.append(f"New snapshot: {snapshot2.timestamp}")
    
    # Compare CPU
    lines.append("\n--- CPU Comparison ---")
    cpu1 = snapshot1.cpu.get("percent", 0)
    cpu2 = snapshot2.cpu.get("percent", 0)
    delta = cpu2 - cpu1
    lines.append(f"CPU Usage: {cpu1:.1f}% → {cpu2:.1f}% (Δ {delta:+.1f}%)")
    
    # Compare Memory
    lines.append("\n--- Memory Comparison ---")
    mem1 = snapshot1.memory.get("virtual", {}).get("percent", 0)
    mem2 = snapshot2.memory.get("virtual", {}).get("percent", 0)
    delta = mem2 - mem1
    lines.append(f"Memory Usage: {mem1}% → {mem2}% (Δ {delta:+}%)")
    
    # Compare Disk
    lines.append("\n--- Disk Comparison ---")
    partitions1 = {p["mountpoint"]: p for p in snapshot1.disk.get("partitions", [])}
    partitions2 = {p["mountpoint"]: p for p in snapshot2.disk.get("partitions", [])}
    
    for mount in set(partitions1.keys()) | set(partitions2.keys()):
        if mount in partitions1 and mount in partitions2:
            pct1 = partitions1[mount].get("percent", 0)
            pct2 = partitions2[mount].get("percent", 0)
            delta = pct2 - pct1
            lines.append(f"{mount}: {pct1}% → {pct2}% (Δ {delta:+}%)")
        elif mount in partitions1:
            lines.append(f"{mount}: REMOVED")
        else:
            lines.append(f"{mount}: ADDED ({partitions2[mount].get('percent', 0)}%)")
    
    # Compare Services count
    lines.append("\n--- Services Comparison ---")
    count1 = len([s for s in snapshot1.services if "name" in s])
    count2 = len([s for s in snapshot2.services if "name" in s])
    delta = count2 - count1
    lines.append(f"Running services: {count1} → {count2} (Δ {delta:+})")
    
    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


def save_snapshot(snapshot: SystemSnapshot, output_dir: Path) -> Path:
    """Save snapshot to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / generate_filename()
    
    with open(output_path, "w") as f:
        f.write(snapshot.to_json())
    
    return output_path


def print_snapshot(snapshot: SystemSnapshot) -> None:
    """Print snapshot in human-readable format."""
    data = snapshot.to_dict()
    
    print("=" * 70)
    print("SYSTEM SNAPSHOT")
    print("=" * 70)
    print(f"Timestamp: {data['timestamp']}")
    
    print("\n--- CPU ---")
    cpu = data["cpu"]
    if "error" in cpu:
        print(f"Error: {cpu['error']}")
    else:
        print(f"Usage: {cpu.get('percent', 'N/A')}%")
        print(f"Cores: {cpu.get('count', 'N/A')}")
        freq = cpu.get("freq")
        if freq and freq.get("current"):
            print(f"Frequency: {freq['current']:.0f} MHz")
    
    print("\n--- Memory ---")
    mem = data["memory"]
    if "error" in mem:
        print(f"Error: {mem['error']}")
    else:
        virt = mem.get("virtual", {})
        swap = mem.get("swap", {})
        print(f"Virtual: {virt.get('percent', 'N/A')}% used ({format_bytes(virt.get('used', 0))} / {format_bytes(virt.get('total', 0))})")
        print(f"Swap: {swap.get('percent', 'N/A')}% used ({format_bytes(swap.get('used', 0))} / {format_bytes(swap.get('total', 0))})")
    
    print("\n--- Disk ---")
    disk = data["disk"]
    if "error" in disk:
        print(f"Error: {disk['error']}")
    else:
        for part in disk.get("partitions", []):
            if "error" in part:
                print(f"{part['mountpoint']}: {part['error']}")
            else:
                print(f"{part['mountpoint']}: {part.get('percent', 'N/A')}% used ({format_bytes(part.get('used', 0))} / {format_bytes(part.get('total', 0))})")
    
    print("\n--- Services ---")
    services = data["services"]
    if services and "error" in services[0]:
        print(f"Error: {services[0]['error']}")
    elif services and "note" in services[0]:
        print(services[0]["note"])
    else:
        print(f"Running services: {len([s for s in services if 'name' in s])}")
    
    print("\n" + "=" * 70)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Capture and compare system state snapshots.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              Capture current system state
  %(prog)s -o /tmp      Save snapshot to /tmp directory
  %(prog)s -c snapshot.json   Compare current state with saved snapshot
  %(prog)s --pretty     Print snapshot in human-readable format
        """,
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path.home() / ".openclaw" / "workspace" / "snapshots",
        help="Output directory for snapshots (default: ~/.openclaw/workspace/snapshots)",
    )
    parser.add_argument(
        "-c", "--compare",
        type=Path,
        metavar="SNAPSHOT_FILE",
        help="Compare current state with a previous snapshot file",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty print the snapshot (default: True)",
    )
    parser.add_argument(
        "--no-pretty",
        action="store_false",
        dest="pretty",
        help="Output raw JSON instead of pretty print",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only output the saved file path",
    )
    
    args = parser.parse_args()
    
    try:
        # Capture current state
        current = SystemSnapshot()
        current.capture()
        
        # If comparing, load the old snapshot and show diff
        if args.compare:
            if not args.compare.exists():
                print(f"Error: Snapshot file not found: {args.compare}", file=sys.stderr)
                return 1
            
            old_snapshot = SystemSnapshot.from_file(args.compare)
            print(compare_snapshots(old_snapshot, current))
            
            # Also save current snapshot
            output_path = save_snapshot(current, args.output)
            if not args.quiet:
                print(f"\nCurrent snapshot saved to: {output_path}")
            else:
                print(output_path)
        else:
            # Save snapshot
            output_path = save_snapshot(current, args.output)
            
            if args.quiet:
                print(output_path)
            else:
                if args.pretty:
                    print_snapshot(current)
                    print(f"\nSnapshot saved to: {output_path}")
                else:
                    print(current.to_json())
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
