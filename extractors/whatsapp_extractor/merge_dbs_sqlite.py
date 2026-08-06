#!/usr/bin/env python3
import sqlite3
import os
import sys
import time
import random
import subprocess

from paths import WHATSAPP_DATA_ROOT, account_db_dir, db_root, decrypted_db_file


class MergeDB:
    def __init__(self):
        pass

    def get_tables(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in cursor.fetchall()]

    def get_columns(self, conn, table):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table});")
        return [column[1] for column in cursor.fetchall()]

    def get_primary_key(self, conn, table):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table});")
        return [column[1] for column in cursor.fetchall() if column[5] > 0]

    def get_foreign_keys(self, conn, table):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        return cursor.fetchall()

    def generate_unique_id(self):
        return f"{int(time.time() * 1000)}{random.randint(1000, 9999)}"

    def generate_unique_text_id(self):
        return f"gen_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

    def is_integer_column(self, conn, table, column):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            if col[1] == column:
                return 'INT' in col[2].upper()
        return False

    def merge_databases(self, db1_path, db2_path):
        if not os.path.exists(db1_path) or not os.path.exists(db2_path):
            print(f"Error: One or both database files don't exist.")
            return False

        conn1 = sqlite3.connect(db1_path)
        conn2 = sqlite3.connect(db2_path)

        conn1.execute("PRAGMA foreign_keys = OFF")
        conn2.execute("PRAGMA foreign_keys = OFF")

        tables1 = self.get_tables(conn1)
        tables2 = self.get_tables(conn2)
        common_tables = set(tables1).intersection(set(tables2))

        print(f"Found {len(common_tables)} common tables between the databases.")
        pk_mapping = {}

        for table in common_tables:
            print(f"Analyzing table: {table}")

            columns1 = self.get_columns(conn1, table)
            columns2 = self.get_columns(conn2, table)

            if set(columns1) != set(columns2):
                print(f"Warning: Columns don't match for table {table}. Skipping.")
                continue

            primary_keys = self.get_primary_key(conn1, table)
            if not primary_keys:
                print(f"Warning: No primary key found for table {table}. Skipping.")
                continue

            pk_mapping[table] = {}
            cursor2 = conn2.cursor()
            cursor2.execute(f"SELECT * FROM {table}")
            rows2 = cursor2.fetchall()

            cursor1 = conn1.cursor()
            cursor1.execute(f"SELECT * FROM {table}")
            rows1 = cursor1.fetchall()

            pk_indices = [columns1.index(pk) for pk in primary_keys]
            non_pk_indices = [i for i in range(len(columns1)) if i not in pk_indices]

            db1_data_map = {}
            db1_pk_values = set()

            for row in rows1:
                non_pk_values = tuple(row[i] for i in non_pk_indices)
                pk_values = tuple(row[i] for i in pk_indices)
                db1_data_map.setdefault(non_pk_values, set()).add(pk_values)
                db1_pk_values.add(pk_values[0] if len(pk_values) == 1 else pk_values)

            for row in rows2:
                pk_values = tuple(row[idx] for idx in pk_indices)
                non_pk_values = tuple(row[i] for i in non_pk_indices)
                if non_pk_values in db1_data_map:
                    continue

                new_pk_values = []
                for i, pk_idx in enumerate(pk_indices):
                    old_pk = pk_values[i]
                    is_int = self.is_integer_column(conn2, table, columns2[pk_idx])
                    if is_int:
                        max_pk = max(db1_pk_values) if db1_pk_values else 0
                        new_pk = int(max_pk) + 1 if str(max_pk).isdigit() else int(self.generate_unique_id())
                    else:
                        new_pk = self.generate_unique_text_id()

                    pk_mapping[table][old_pk] = new_pk
                    new_pk_values.append(new_pk)
                    db1_pk_values.add(new_pk)

        for table in common_tables:
            if table not in pk_mapping:
                continue

            print(f"Processing table: {table}")
            columns1 = self.get_columns(conn1, table)
            primary_keys = self.get_primary_key(conn1, table)
            if not primary_keys:
                continue

            foreign_keys = self.get_foreign_keys(conn2, table)
            cursor2 = conn2.cursor()
            cursor2.execute(f"SELECT * FROM {table}")
            rows2 = cursor2.fetchall()

            pk_indices = [columns1.index(pk) for pk in primary_keys]
            non_pk_indices = [i for i in range(len(columns1)) if i not in pk_indices]

            cursor1 = conn1.cursor()
            cursor1.execute(f"SELECT * FROM {table}")
            rows1 = cursor1.fetchall()
            db1_data_map = {tuple(row[i] for i in non_pk_indices): True for row in rows1}

            columns_str = ", ".join([f"\"{col}\"" for col in columns1])
            placeholders = ", ".join(["?" for _ in columns1])
            insert_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

            inserted_count, skipped_count, error_count = 0, 0, 0

            for row in rows2:
                row_list = list(row)
                non_pk_values = tuple(row[i] for i in non_pk_indices)

                if non_pk_values in db1_data_map:
                    skipped_count += 1
                    continue

                for i, pk_idx in enumerate(pk_indices):
                    old_pk = row[pk_idx]
                    if old_pk in pk_mapping[table]:
                        row_list[pk_idx] = pk_mapping[table][old_pk]

                for fk in foreign_keys:
                    fk_col_idx = columns1.index(fk[3])
                    ref_table = fk[2]
                    old_fk_value = row[fk_col_idx]
                    if ref_table in pk_mapping and old_fk_value in pk_mapping[ref_table]:
                        row_list[fk_col_idx] = pk_mapping[ref_table][old_fk_value]

                try:
                    cursor1.execute(insert_query, row_list)
                    conn1.commit()
                    inserted_count += 1
                    db1_data_map[non_pk_values] = True
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        error_count += 1
                        skipped_count += 1
                    else:
                        print(f"IntegrityError for table {table}: {e}")
                        raise
                except Exception as e:
                    print(f"Error inserting into {table}: {e}")
                    raise

            print(f"Table {table}: Inserted {inserted_count} rows, skipped {skipped_count} (errors: {error_count})")

        conn1.execute("PRAGMA foreign_keys = ON")
        conn1.close()
        conn2.close()

        print("\nMerge completed successfully!")
        return True

    def get_adb_devices(self):
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            lines = result.stdout.strip().splitlines()[1:]
            devices = [line.split()[0] for line in lines if 'device' in line]
            return devices
        except Exception as e:
            print(f"Failed to get adb devices: {e}")
            return []

    def merge_db_whatsapp(self):
        try:
            devices = self.get_adb_devices()
            if not devices:
                print("No ADB devices detected.")
                sys.exit(1)

            for device_id in devices:
                db2_path = os.path.join(db_root(device_id), f"{device_id}.db")
                db1_path = os.path.join(account_db_dir(device_id, "_account1"), f"{device_id}_account1.db")

                if os.path.exists(db2_path):
                    print(f"Detected pulled DB for device {device_id}")
                    if not os.path.exists(db1_path):
                        os.makedirs(os.path.dirname(db1_path), exist_ok=True)
                        print(f"No existing DB found. Moving pulled DB to {db1_path}")
                        os.rename(db2_path, db1_path)
                    else:
                        print(f"Merging pulled DB into existing DB for {device_id}")
                        merger = MergeDB()
                        success = merger.merge_databases(db1_path, db2_path)
                        if success:
                            if os.path.exists(db2_path):
                                try:
                                    os.remove(db2_path)
                                    print(f"Successfully deleted backup DB: {db2_path}")
                                except Exception as e:
                                    print(f"Failed to delete backup DB: {e}")
                            else:
                                print(f"Backup DB already deleted or not found: {db2_path}")
                else:
                    print(f"No pulled DB found for device {device_id}. Skipping...")
        except Exception as e:
            print(f"An error occurred during processing: {e}")

