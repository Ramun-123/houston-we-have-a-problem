import json
import csv
import os
from pathlib import Path
from typing import Iterable, Dict, Any, Optional, List

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def read_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def append_csv(path: str | Path, rows: Iterable[Iterable[Any]], header: Optional[List[str]] = None) -> None:
    ensure_dir(Path(path).parent)
    file_exists = Path(path).exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header and not file_exists:
            writer.writerow(header)
        for r in rows:
            writer.writerow(list(r))

def list_files(path: str | Path, suffix: str) -> list[Path]:
    base = Path(path)
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_file() and p.suffix == suffix])

def atomic_write(path: str | Path, content: str) -> None:
    ensure_dir(Path(path).parent)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, path)

def read_text(path: str | Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()