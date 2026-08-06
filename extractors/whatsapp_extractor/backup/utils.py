import argparse
import io
import zlib

HEADER_SIZE = 384
DEFAULT_DATA_OFFSET = 122
DEFAULT_IV_OFFSET = 8


def from_hex(logger, string: str) -> bytes:
    if len(string) != 64:
        logger.f(f"Key must be 64 characters, not {len(string)}.")
    barr = b""
    try:
        barr = bytes.fromhex(string)
    except ValueError as e:
        logger.f(f"Invalid hex string. Exception: {e}")
    if len(barr) != 32:
        logger.e(f"Key is {len(barr)} bytes, expected 32.")
    return barr


def parsecmdline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decrypt WhatsApp backup files crypt15.")
    parser.add_argument("hexkey", nargs="?", type=str, help="Hex encoded key.")
    parser.add_argument(
        "encrypted",
        nargs="?",
        type=argparse.FileType("rb"),
        default="msgstore.db.crypt15",
        help="Encrypted file (default: msgstore.db.crypt15).",
    )
    parser.add_argument(
        "decrypted",
        nargs="?",
        type=argparse.FileType("wb"),
        default="msgstore.db",
        help="Decrypted output file (default: msgstore.db).",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Make errors non-fatal (default: false).")
    parser.add_argument(
        "-nm", "--no-mem", action="store_true", help="Do not load files in RAM (default: load into RAM)."
    )
    parser.add_argument(
        "-bs", "--buffer-size", type=int, help=f"Bytes to process at a time (default: {io.DEFAULT_BUFFER_SIZE})."
    )
    parser.add_argument("-ng", "--no-guess", action="store_true", help="Do not guess offsets, only use protobuf.")
    parser.add_argument("-np", "--no-protobuf", action="store_true", help="Do not parse protobuf, only guess offsets.")
    parser.add_argument(
        "-ivo",
        "--iv-offset",
        type=int,
        default=DEFAULT_IV_OFFSET,
        help=f"Default IV offset (default: {DEFAULT_IV_OFFSET}).",
    )
    parser.add_argument(
        "-do",
        "--data-offset",
        type=int,
        default=DEFAULT_DATA_OFFSET,
        help=f"Default data offset (default: {DEFAULT_DATA_OFFSET}).",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print all messages.")
    return parser.parse_args()


def javaintlist2bytes(barr: list) -> bytes:
    return b"".join(i.to_bytes(1, byteorder="big", signed=True) for i in barr)


def test_decompression(logger, test_data: bytes) -> bool:
    if test_data[:4] == b"PK\x03\x04":
        return True
    try:
        zlib_obj = zlib.decompressobj().decompress(test_data)
        if len(zlib_obj) < 16:
            logger.e("Decompressed chunk too small")
            return False
        if zlib_obj[:15].decode("ascii") != "SQLite format 3":
            logger.e("Decryption OK, but not a valid SQLite database")
            return logger.force
        return True
    except zlib.error:
        return False


def oscillate(n: int, n_min: int, n_max: int):
    if n_min < 0:
        n_min = 0

    i, c = n, 1
    while True:
        if i == n_max:
            break
        yield i
        i -= c
        c += 1
        if i == 0 or i == n_min:
            break
        yield i
        i += c
        c += 1

    if i == n_min and n != i / 2:
        yield i
        for j in range(i + c, n_max + 1):
            yield j

    if i == n_max and n != i / 2:
        yield n_max
        for j in range(i - c, n_min - 1, -1):
            yield j
