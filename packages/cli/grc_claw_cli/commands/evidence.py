"""Evidence management commands for GRC_Claw CLI."""
import argparse
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from grc_claw_cli.utils.output import print_json, print_table, print_success, print_error, print_warning, print_info
from grc_claw_cli.utils.config import Config


class EvidenceStore:
    """Evidence store with SHA-256 hashing and lineage tracking."""

    def __init__(self):
        self.config = Config()
        self.evidence_dir = Path(self.config.get("evidence_dir", "./compliance-evidence"))
        self.records = []
        self._load()

    def _load(self):
        index_file = self.evidence_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file) as f:
                    self.records = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.records = []

    def _save(self):
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        index_file = self.evidence_dir / "index.json"
        with open(index_file, "w") as f:
            json.dump(self.records, f, indent=2, default=str)

    @staticmethod
    def hash_content(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def attach(self, control_id, uri, content=None, tenant_id=1, source="cli"):
        sha256 = self.hash_content(content) if content else hashlib.sha256(f"{uri}|{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()
        record = {
            "id": f"ev-{sha256[:16]}",
            "control_id": control_id,
            "tenant_id": tenant_id,
            "sha256": sha256,
            "uri": uri,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "lineage": {"parent_hash": None, "source": source},
        }
        self.records.append(record)
        self._save()
        return record

    def get(self, evidence_id):
        return next((r for r in self.records if r["id"] == evidence_id), None)

    def list(self, control_id=None):
        if control_id:
            return [r for r in self.records if r["control_id"] == control_id]
        return self.records

    def verify(self, evidence_id):
        record = self.get(evidence_id)
        if not record:
            return None
        # Verify hash integrity
        file_path = Path(record["uri"])
        if file_path.exists():
            content = file_path.read_bytes()
            current_hash = self.hash_content(content)
            return {
                "id": evidence_id,
                "valid": current_hash == record["sha256"],
                "stored_hash": record["sha256"],
                "current_hash": current_hash,
                "uri": record["uri"],
            }
        return {
            "id": evidence_id,
            "valid": False,
            "stored_hash": record["sha256"],
            "current_hash": None,
            "uri": record["uri"],
            "error": "File not found",
        }

    def delete(self, evidence_id):
        record = self.get(evidence_id)
        if not record:
            return False
        self.records = [r for r in self.records if r["id"] != evidence_id]
        self._save()
        return True

    def stats(self):
        controls = set(r["control_id"] for r in self.records)
        return {
            "total_evidence": len(self.records),
            "unique_controls": len(controls),
            "controls": sorted(controls),
        }


def register(subparsers):
    """Register evidence subcommands."""
    parser = subparsers.add_parser("evidence", help="Evidence management commands")
    ev_sub = parser.add_subparsers(dest="evidence_command", help="Evidence operations")

    # evidence attach
    attach_p = ev_sub.add_parser("attach", help="Attach evidence for a control")
    attach_p.add_argument("--control-id", required=True, help="Control ID")
    attach_p.add_argument("--uri", required=True, help="Evidence URI or file path")
    attach_p.add_argument("--file", help="File to hash and attach")
    attach_p.add_argument("--tenant-id", type=int, default=1, help="Tenant ID")
    attach_p.add_argument("--source", default="cli", help="Evidence source")

    # evidence list
    list_p = ev_sub.add_parser("list", help="List evidence records")
    list_p.add_argument("--control-id", help="Filter by control ID")
    list_p.add_argument("--json", action="store_true", help="Output as JSON")

    # evidence get
    get_p = ev_sub.add_parser("get", help="Get evidence record")
    get_p.add_argument("id", help="Evidence ID")
    get_p.add_argument("--json", action="store_true", help="Output as JSON")

    # evidence verify
    verify_p = ev_sub.add_parser("verify", help="Verify evidence integrity")
    verify_p.add_argument("id", help="Evidence ID")
    verify_p.add_argument("--json", action="store_true", help="Output as JSON")

    # evidence delete
    delete_p = ev_sub.add_parser("delete", help="Delete evidence record")
    delete_p.add_argument("id", help="Evidence ID")

    # evidence stats
    stats_p = ev_sub.add_parser("stats", help="Show evidence statistics")
    stats_p.add_argument("--json", action="store_true", help="Output as JSON")


def handle(args, config: Config):
    """Handle evidence commands."""
    store = EvidenceStore()
    cmd = args.evidence_command

    if cmd == "attach":
        content = None
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print_error(f"File not found: {args.file}")
                return 1
            content = file_path.read_bytes()
        record = store.attach(
            control_id=args.control_id,
            uri=args.uri,
            content=content,
            tenant_id=args.tenant_id,
            source=args.source,
        )
        print_success(f"Evidence attached: {record['id']}")
        print_json(record)
        return 0

    elif cmd == "list":
        records = store.list(control_id=args.control_id)
        if args.json:
            print_json(records)
        else:
            if not records:
                print_info("No evidence records found.")
            else:
                rows = [[r["id"][:12], r["control_id"], r["collected_at"][:10], r["uri"][:40]] for r in records]
                print_table(["ID", "Control", "Date", "URI"], rows)
        return 0

    elif cmd == "get":
        record = store.get(args.id)
        if not record:
            print_error(f"Evidence not found: {args.id}")
            return 1
        print_json(record)
        return 0

    elif cmd == "verify":
        result = store.verify(args.id)
        if not result:
            print_error(f"Evidence not found: {args.id}")
            return 1
        if result.get("valid"):
            print_success(f"Evidence {args.id} is valid")
        else:
            print_error(f"Evidence {args.id} FAILED verification")
            if result.get("error"):
                print_error(f"  Error: {result['error']}")
        print_json(result)
        return 0 if result.get("valid") else 1

    elif cmd == "delete":
        if store.delete(args.id):
            print_success(f"Evidence deleted: {args.id}")
            return 0
        print_error(f"Evidence not found: {args.id}")
        return 1

    elif cmd == "stats":
        stats = store.stats()
        if args.json:
            print_json(stats)
        else:
            print_info("Evidence Statistics")
            print(f"  Total evidence records: {stats['total_evidence']}")
            print(f"  Unique controls: {stats['unique_controls']}")
            if stats["controls"]:
                print(f"  Controls: {', '.join(stats['controls'])}")
        return 0

    else:
        print_error("No evidence subcommand specified. Use: grc evidence <attach|list|get|verify|delete|stats>")
        return 1
