from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def calculate_sha256(content: str) -> str:
    """Compute SHA-256 hex digest of file text content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_manifest(
    run_id: str,
    client_code: str,
    status: str,
    files: Dict[str, str],
) -> Dict[str, Any]:
    """Generate structured SHA-256 cryptographic manifest."""
    files_list: List[Dict[str, Any]] = []

    for rel_path, content in sorted(files.items()):
        files_list.append({
            "path": rel_path,
            "sha256": calculate_sha256(content),
            "size_bytes": len(content.encode("utf-8")),
        })

    manifest: Dict[str, Any] = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "client_code": client_code,
        "verification_status": status,
        "total_files": len(files_list),
        "files": files_list,
    }
    return manifest


def write_manifest_file(workspace_dir: Path, manifest: Dict[str, Any]) -> Path:
    """Save VERIFICATION_MANIFEST.json directly in the workspace root."""
    manifest_path = workspace_dir / "VERIFICATION_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path

