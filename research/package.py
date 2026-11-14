"""Package current research sources and measured artifacts with a hash manifest."""
import hashlib
import json
from pathlib import Path
import zipfile


root = Path(__file__).resolve().parents[1]
destination = root / "research" / "results" / "guardianai-research.zip"
manifest_path = root / "research" / "results" / "delivery-manifest.json"
files = sorted(path for path in root.rglob("*") if path.is_file()
               and not any(part in {".git", "__pycache__"} for part in path.relative_to(root).parts)
               and path not in {destination, manifest_path})
manifest = {"scope": "Research source, reports, original pilot evidence, and measured trace archive",
            "files": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in files}}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in files + [manifest_path]:
        archive.write(path, path.relative_to(root).as_posix())
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
    for name, expected in manifest["files"].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == expected, name
print(json.dumps({"zip": str(destination), "files": len(files) + 1,
                  "zip_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                  "verification": "ZIP CRC and all manifest file hashes passed"}))
