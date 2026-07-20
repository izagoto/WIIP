#!/usr/bin/env python3
"""Export SQLite tables to a single Excel file."""

import re
import sqlite3
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font
from datetime import datetime
DB_DIR = Path(__file__).parent / "extractors" / "whatsapp_extractor" / "db_whatsapp"
OUTPUT_DIR = Path(__file__).parent / "export"
MAX_SHEET_NAME_LEN = 31
INDEX_SHEET_NAME = "INDEX"
ILLEGAL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def sanitize_cell(value):
    if pd.isna(value):
        return "NULL"
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    if isinstance(value, str):
        return ILLEGAL_CHAR_RE.sub("", value)
    return value


def sanitize_sheet_name(name: str, used: set[str]) -> str:
    name = re.sub(r"[\[\]:*?/\\]", "_", name)[:MAX_SHEET_NAME_LEN]
    if not name:
        name = "sheet"
    base = name
    i = 1
    while name in used:
        suffix = f"_{i}"
        name = base[: MAX_SHEET_NAME_LEN - len(suffix)] + suffix
        i += 1
    used.add(name)
    return name


def get_tables(conn: sqlite3.Connection) -> list[str]:
    cur = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    return [row[0] for row in cur.fetchall()]


def get_row_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


def build_sheet_names(tables: list[str]) -> dict[str, str]:
    used: set[str] = {INDEX_SHEET_NAME}
    return {table: sanitize_sheet_name(table, used) for table in tables}


def build_index(
    tables: list[str],
    row_counts: dict[str, int],
    sheet_names: dict[str, str],
) -> pd.DataFrame:
    rows = []
    for i, table in enumerate(tables, start=1):
        count = row_counts[table]
        has_data = count > 0
        rows.append(
            {
                "no": i,
                "table": table,
                "baris": count,
                "status": "ada data" if has_data else "kosong",
                "sheet": sheet_names[table] if has_data else "-",
            }
        )
    return pd.DataFrame(rows)


def convert_timestamp(val):
    if pd.isna(val) or val == "NULL" or val == "":
        return val
    try:
        val_int = int(val)
        if val_int == 0:
            return "NULL"
        # Jika digit > 11, asumsikan milidetik (ms)
        if val_int > 99999999999:
            dt = datetime.fromtimestamp(val_int / 1000.0)
        else:
            dt = datetime.fromtimestamp(val_int)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError, OSError, OverflowError):
        return val


def read_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    df = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    for col in df.columns:
        col_lower = col.lower()
        if 'timestamp' in col_lower or 'date' in col_lower:
            df[col] = df[col].apply(convert_timestamp)
        df[col] = df[col].map(sanitize_cell)
    return df


def format_worksheet(ws):
    ws.freeze_panes = "A2"
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col in ws.columns:
        max_length = 0
        column_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    lines = str(cell.value).split('\n')
                    for line in lines:
                        max_length = max(max_length, len(line))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width


def process_database(db_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(exist_ok=True, parents=True)
    conn = sqlite3.connect(db_path)
    tables = get_tables(conn)

    print(f"Database: {db_path.name}")
    print(f"Total tabel: {len(tables)}")

    row_counts = {table: get_row_count(conn, table) for table in tables}
    tables_with_data = [t for t in tables if row_counts[t] > 0]
    sheet_names = build_sheet_names(tables_with_data)

    index_df = build_index(tables, row_counts, sheet_names)
    print(
        f"Tabel berisi data: {len(tables_with_data)} | "
        f"kosong: {len(tables) - len(tables_with_data)}"
    )
    print(f"\nMenulis {output_path.name} ({1 + len(tables_with_data)} sheet)...")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        index_df.to_excel(writer, sheet_name=INDEX_SHEET_NAME, index=False)
        format_worksheet(writer.sheets[INDEX_SHEET_NAME])
        print(f"  INDEX: {len(index_df)} tabel")

        for table in tables_with_data:
            df = read_table(conn, table)
            sheet = sheet_names[table]
            df.to_excel(writer, sheet_name=sheet, index=False)
            format_worksheet(writer.sheets[sheet])
            print(f"  {table}: {len(df)} baris -> sheet '{sheet}'")

    conn.close()
    print(f"\nSelesai! -> {output_path}\n" + "-" * 40 + "\n")


def main() -> None:
    if not DB_DIR.exists():
        raise SystemExit(f"Direktori database tidak ditemukan: {DB_DIR}")

    db_files = list(DB_DIR.glob("*.db"))
    if not db_files:
        print(f"Tidak ada file .db ditemukan di: {DB_DIR}")
        return

    for db_file in db_files:
        output_file = OUTPUT_DIR / f"{db_file.stem}.xlsx"
        process_database(db_file, output_file)


if __name__ == "__main__":
    main()
