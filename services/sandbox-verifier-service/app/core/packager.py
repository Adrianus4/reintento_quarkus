import os
from pathlib import Path
from typing import Dict
import zipfile


def materialize_files(base_dir: Path, files: Dict[str, str]) -> None:
    """
    Safely write files into base_dir, strictly blocking path traversal attempts.
    """
    base_dir_resolved = base_dir.resolve()
    base_dir_resolved.mkdir(parents=True, exist_ok=True)

    for rel_path, content in files.items():
        # Prevent absolute paths or empty paths
        p = Path(rel_path.strip())
        if p.is_absolute():
            raise ValueError(f"Absolute paths not permitted: '{rel_path}'")

        target_file = (base_dir_resolved / p).resolve()

        # Strict Path Traversal defense
        try:
            target_file.relative_to(base_dir_resolved)
        except ValueError:
            raise ValueError(f"Path traversal detected in path: '{rel_path}'")

        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")


def create_zip_archive(workspace_dir: Path, output_zip_path: Path) -> Path:
    """
    Compress the workspace into a zip file, preserving relative folder hierarchies.
    """
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, filenames in os.walk(workspace_dir):
            for filename in filenames:
                file_path = Path(root) / filename
                # Exclude the zip file itself if placed inside
                if file_path.resolve() == output_zip_path.resolve():
                    continue
                rel_path = file_path.relative_to(workspace_dir)
                zip_file.write(file_path, arcname=str(rel_path))

    return output_zip_path

