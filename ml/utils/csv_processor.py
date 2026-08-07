import csv
import re
from pathlib import Path


def read_csv_text(path: Path) -> str:
    rows: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            rows.append(", ".join(cell.strip() for cell in row if cell.strip()))
    return "\n".join(rows)


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
