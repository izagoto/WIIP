import io
import zlib
from hashlib import md5, sha256
import javaobj.v2 as javaobj
from re import findall
from Cryptodome.Cipher import AES
from google.protobuf.message import DecodeError
import argparse
import hmac
import sys
import os

sys.path.append(os.path.dirname(__file__))

import proto.prefix_pb2 as prefix


HEADER_SIZE = 384
DEFAULT_DATA_OFFSET = 122
DEFAULT_IV_OFFSET = 8


# Logger class
class Log:
    def __init__(self, verbose: bool, force: bool):
        self.verbose = verbose
        self.force = force

    def v(self, msg: str):
        if self.verbose:
            print(f"[V] {msg}")

    @staticmethod
    def i(msg: str):
        print(f"[I] {msg}")

    def e(self, msg: str):
        print(f"[E] {msg}")
        if not self.force:
            print('To bypass checks, use the "--force" parameter')
            exit(1)

    @staticmethod
    def f(msg: str):
        print(f"[F] {msg}")
        exit(1)


# Key class
class Key:
    SUPPORTED_CIPHER_VERSION = b"\x00\x01"
    SUPPORTED_KEY_VERSIONS = [b"\x01", b"\x02", b"\x03"]
    BACKUP_ENCRYPTION = b"backup encryption\x01"

    def is_crypt15(self):
        return self.key_version is None

    def __str__(self):
        try:
            string = "Key("
            if self.key is not None:
                string += f"key: {self.key.hex()}"
            if self.serversalt is not None:
                string += f" , serversalt: {self.serversalt.hex()}"
            if self.key_version is not None:
                string += f" , key_version: {self.key_version.hex()}"
            if self.cipher_version is not None:
                string += f" , cipher_version: {self.cipher_version.hex()}"
            return string + ")"
        except Exception as e:
            return f"Exception printing key: {e}"

    def __init__(self, logger, key_file_name):
        self.key = None  # type: ignore
        self.serversalt = None  # type: ignore
        self.key_version = None  # type: ignore
        self.cipher_version = None  # type: ignore

        hexkey = b""

        logger.v("Reading hexkey...")

        try:
            key_file_stream = open(key_file_name, "rb")
            try:
                java_data = getattr(javaobj.load(key_file_stream), "data", [])
                hexkey = javaintlist2bytes(java_data)
            except (ValueError, RuntimeError) as e:
                logger.f(f"The hexkey is not a valid Java object: {e}")

        except OSError:
            hexkey = from_hex(logger, key_file_name)

        if len(hexkey) == 131:
            self.load_crypt14(logger, keyfile=hexkey)
        elif len(hexkey) == 32:
            self.load_crypt15(logger, hexkey=hexkey)
        else:
            logger.f("Unrecognized key file format.")

    def load_crypt14(self, logger, keyfile: bytes):
        self.cipher_version = keyfile[: len(self.SUPPORTED_CIPHER_VERSION)]
        if self.SUPPORTED_CIPHER_VERSION != self.cipher_version:
            logger.e(
                "Invalid keyfile: Unsupported cipher version {}".format(
                    keyfile[: len(self.SUPPORTED_CIPHER_VERSION)].hex()
                )
            )
        index = len(self.SUPPORTED_CIPHER_VERSION)

        version_supported = False
        for v in self.SUPPORTED_KEY_VERSIONS:
            if v == keyfile[index : index + len(self.SUPPORTED_KEY_VERSIONS[0])]:  # noqa
                version_supported = True
                self.key_version = v
                break
        if not version_supported:
            logger.e(
                "Invalid keyfile: Unsupported key version {}".format(
                    keyfile[index : index + len(self.SUPPORTED_KEY_VERSIONS[0])].hex()  # noqa
                )
            )

        self.serversalt = keyfile[3:35]
        padding = keyfile[83:99]
        for byte in padding:
            if byte:
                logger.e("Invalid keyfile: IV is not zeroed out but is: {}".format(padding.hex()))
                break

        self.key = keyfile[99:]

        logger.i("Crypt12 & 14 key loaded")

    def load_crypt15(self, logger, hexkey: bytes):
        if len(hexkey) != 32:
            logger.f("Crypt15 loader trying to load key")

        self.key = hmac.new(b"\x00" * 32, hexkey, sha256).digest()
        self.key = hmac.new(self.key, self.BACKUP_ENCRYPTION, sha256).digest()

        logger.i("Crypt15 key loaded")


# Utils functions
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
    parser = argparse.ArgumentParser(description="Decrypt WhatsApp Chat Files (.crypt15 format).")
    parser.add_argument("key", nargs="?", type=str)
    parser.add_argument("ciphertext", nargs="?", type=argparse.FileType("rb"), default="msgstore.db.crypt15")
    parser.add_argument("plaintext", nargs="?", type=argparse.FileType("wb"), default="msgstore.db")

    parser.add_argument("-f", "--force", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-nm", "--no-mem", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-bs", "--buffer-size", type=int, help=argparse.SUPPRESS)
    parser.add_argument("-np", "--no-protobuf", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-ng", "--no-guess", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-ivo", "--iv-offset", type=int, default=DEFAULT_IV_OFFSET, help=argparse.SUPPRESS)
    parser.add_argument("-do", "--data-offset", type=int, default=DEFAULT_DATA_OFFSET, help=argparse.SUPPRESS)
    parser.add_argument("-v", "--verbose", action="store_true", help=argparse.SUPPRESS)

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


# Decryptor functions
def decrypt(logger, file_hash, cipher, encrypted, decrypted, buffer_size: int = 0):
    z_obj = zlib.decompressobj()
    if cipher is None:
        logger.f("No cipher created")
    try:
        if buffer_size == 0:
            try:
                encrypted_data = encrypted.read()
                crypt12_footer = str(encrypted_data[-4:])
                jid = findall(r"(?:-|\d)(?:-|\d)(\d\d)", crypt12_footer)

                if len(jid) == 1:
                    encrypted_data = encrypted_data[:-4]
                    logger.v(f"Phone number ends with {jid[0]}")

                checksum = encrypted_data[-16:]
                authentication_tag = encrypted_data[-32:-16]
                encrypted_data = encrypted_data[:-32]
                is_multifile_backup = False
                file_hash.update(encrypted_data)
                file_hash.update(authentication_tag)

                if file_hash.digest() != checksum:
                    is_multifile_backup = True
                else:
                    logger.v("Checksum OK. Decrypting...")

                output_decrypted = b""
                try:
                    output_decrypted = cipher.decrypt(encrypted_data)
                except ValueError as e:
                    logger.f(f"Decryption failed: {e}. Backup corrupted.")

                try:
                    if is_multifile_backup:
                        output_decrypted += cipher.decrypt(authentication_tag)
                        cipher.verify(checksum)
                    else:
                        cipher.verify(authentication_tag)
                except ValueError as e:
                    logger.e(f"Tag mismatch: {e}. Backup corrupted.")

                try:
                    output_file = z_obj.decompress(output_decrypted)
                    if not z_obj.eof:
                        logger.e("Database truncated.")
                except zlib.error:
                    output_file = output_decrypted

                    if test_decompression(logger, output_file[: io.DEFAULT_BUFFER_SIZE]):
                        logger.i("Decrypted data is ZIP. Not decompressing.")
                    else:
                        logger.e("Unrecognized decrypted data. Key mismatch.")
                decrypted.write(output_file)
            except MemoryError:
                logger.f("Out of RAM. Use -nm.")
        else:
            if buffer_size < 17:
                logger.i(f"Invalid buffer size, using {io.DEFAULT_BUFFER_SIZE}")
                buffer_size = io.DEFAULT_BUFFER_SIZE
            is_zip = True
            chunk = None
            logger.v("Decrypting...")

            while True:
                next_chunk = None
                checksum = None
                if chunk is None:
                    try:
                        chunk = encrypted.read(buffer_size)
                    except MemoryError:
                        logger.f("Out of RAM. Use smaller buffer size.")
                    if chunk is not None and len(chunk) < buffer_size:
                        logger.f("Buffer size too large. Use smaller buffer.")
                    continue
                try:
                    next_chunk = encrypted.read(buffer_size)
                except MemoryError:
                    logger.f("Out of RAM. Use smaller buffer size.")

                if next_chunk is not None and len(next_chunk) <= 36:
                    if len(next_chunk) == 36:
                        checksum = next_chunk
                    elif len(next_chunk) == 0:
                        checksum = chunk[-36:]
                        chunk = chunk[:-36]
                    else:
                        checksum = chunk[-(36 - len(next_chunk)) :] + next_chunk
                        chunk = chunk[: -(36 - len(next_chunk))]

                file_hash.update(chunk)
                decrypted_chunk = cipher.decrypt(chunk)

                if is_zip:
                    try:
                        decrypted.write(z_obj.decompress(decrypted_chunk))
                    except zlib.error:
                        if test_decompression(logger, decrypted_chunk):
                            logger.i("Decrypted data is ZIP. Not decompressing.")
                        else:
                            logger.e("Unrecognized decrypted data. Key mismatch.")
                        is_zip = False
                        decrypted.write(decrypted_chunk)
                else:
                    decrypted.write(decrypted_chunk)

                if checksum is not None:
                    is_multifile_backup = False
                    crypt12_footer = str(checksum[-4:])
                    jid = findall(r"(?:-|\d)(?:-|\d)(\d\d)", crypt12_footer)

                    if len(jid) == 1:
                        checksum = checksum[:-4]
                        logger.v(f"Phone number ends with {jid[0]}")
                    else:
                        chunk = checksum[:4]
                        file_hash.update(chunk)
                        decrypted_chunk = cipher.decrypt(chunk)

                        if is_zip:
                            try:
                                decrypted.write(z_obj.decompress(decrypted_chunk))
                            except zlib.error:
                                logger.e("Backup corrupted.")
                                decrypted.write(decrypted_chunk)
                        else:
                            decrypted.write(decrypted_chunk)
                        checksum = checksum[4:]
                    file_hash.update(checksum[:16])

                    if file_hash.digest() != checksum[16:]:
                        is_multifile_backup = True
                    else:
                        logger.v(f"Checksum OK ({file_hash.hexdigest()})!")

                    try:
                        if is_multifile_backup:
                            decrypted.write(cipher.decrypt(checksum[:16]))
                            cipher.verify(checksum[16:])
                        else:
                            cipher.verify(checksum[:16])
                    except ValueError as e:
                        logger.e(f"Tag mismatch: {e}. Backup corrupted.")
                    break

                chunk = next_chunk

            if is_zip and not z_obj.eof:
                if not logger.force:
                    decrypted.truncate(0)
                logger.e("Database truncated.")

        decrypted.flush()
    except OSError as e:
        logger.f(f"I/O error: {e}")
    finally:
        decrypted.close()
        encrypted.close()


def parse_protobuf(logger, file_hash, key, encrypted):
    # try:
    #     import proto.prefix_pb2 as prefix
    # except ImportError as e:
    #     logger.e(f"Import error: {e}")
    #     return None
    # except AttributeError as e:
    #     logger.e(f"Proto classes error: {e}. Update protobuf to 3.20.0+.")
    #     return None

    p = prefix.prefix()  # type: ignore
    logger.v("Parsing header...")

    try:
        protobuf_size = encrypted.read(1)
        file_hash.update(protobuf_size)
        protobuf_size = int.from_bytes(protobuf_size, byteorder="big")
        backup_type_raw = encrypted.read(1)
        backup_type = int.from_bytes(backup_type_raw, byteorder="big")
        if backup_type != 1:
            if backup_type == 8:
                logger.v("Not a recent msgstore")
                encrypted.seek(-1, 1)
            else:
                logger.e(f"Unexpected type: {backup_type}")
        else:
            file_hash.update(backup_type_raw)

        try:
            protobuf_raw = encrypted.read(protobuf_size)
            file_hash.update(protobuf_raw)
            if p.ParseFromString(protobuf_raw) != protobuf_size:
                logger.e("Protobuf not fully read.")
            else:
                version = findall(r"\d(?:\.\d{1,3}){3}", p.info.whatsapp_version)
                if len(version) != 1:
                    logger.e("WhatsApp version not found")
                else:
                    logger.v(f"WhatsApp version: {version[0]}")
                if len(p.info.substringedUserJid) != 2:
                    logger.e("Phone number end not 2 characters")
                logger.v(f"Phone number ends with {p.info.substringedUserJid}")
                if len(p.c15_iv.IV) != 0:
                    if not key.is_crypt15():
                        logger.e("Using crypt14 key with crypt15 backup.")
                    if len(p.c15_iv.IV) != 16:
                        logger.e(f"IV length {len(p.c15_iv.IV)}")
                    iv = p.c15_iv.IV
                elif len(p.c14_cipher.IV) != 0:
                    if key.is_crypt15():
                        logger.f("Using crypt15 key with crypt14 backup.")
                    key.key_version = (key.key_version[0] + 48).to_bytes(1, byteorder="big")
                    if key.key_version != p.c14_cipher.key_version:
                        if key.key_version > p.c14_cipher.key_version:
                            logger.e(
                                f"Key version mismatch: {key.key_version} != {p.c14_cipher.key_version}. Backup too old for this key."  # noqa
                            )
                        elif key.key_version < p.c14_cipher.key_version:
                            logger.e(
                                f"Key version mismatch: {key.key_version} != {p.c14_cipher.key_version}. Backup too new for this key."  # noqa
                            )
                        else:
                            logger.e(f"Key version mismatch: {key.key_version} != {p.c14_cipher.key_version}.")
                    if key.serversalt != p.c14_cipher.server_salt:
                        logger.e(f"Server salt mismatch: {key.serversalt} != {p.c14_cipher.server_salt}")
                    if len(p.c14_cipher.IV) != 16:
                        logger.e(f"IV length {len(p.c14_cipher.IV)}")
                    iv = p.c14_cipher.IV
                else:
                    logger.e("Could not parse IV from protobuf.")
                    return None
                logger.i("Database header parsed")
                return AES.new(key.key, AES.MODE_GCM, iv)
        except DecodeError as e:
            print(e)
    except OSError as e:
        logger.f(f"Header read failed: {e}")
    logger.e("Could not parse protobuf.")

    return None


def find_data_offset(logger, header, iv_offset, key, starting_data_offset):
    iv = header[iv_offset : iv_offset + 16]  # noqa
    for i in oscillate(n=starting_data_offset, n_min=iv_offset + len(iv), n_max=HEADER_SIZE - 128):
        cipher = AES.new(key, AES.MODE_GCM, iv)
        test_bytes = cipher.decrypt(header[i : i + 2])  # noqa
        for zheader in [b"x\x01", b"PK"]:
            if test_bytes == zheader:
                cipher = AES.new(key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt(header[i:])
                if test_decompression(logger, decrypted):
                    return i
    return -1


def guess_offsets(logger, key, file_hash, encrypted, def_iv_offset, def_data_offset):
    db_header, data_offset, iv_offset = None, None, None
    encrypted.seek(0)
    db_header = encrypted.read(HEADER_SIZE)

    if len(db_header) < HEADER_SIZE:
        logger.f("Encrypted database too small. Keyfile and database swapped?")

    try:
        if db_header[:15].decode("ascii") == "SQLite format 3":
            logger.e("Database not encrypted. Input and output files swapped?")
    except ValueError:
        pass

    version = findall(b"\\d(?:\\.\\d{1,3}){3}", db_header)
    if len(version) != 1:
        logger.i("WhatsApp version not found (Crypt12?)")
    else:
        logger.v(f"WhatsApp version: {version[0].decode('ascii')}")

    for iv_offset in oscillate(n=def_iv_offset, n_min=0, n_max=HEADER_SIZE - 128):
        data_offset = find_data_offset(logger, db_header, iv_offset, key, def_data_offset)
        if data_offset != -1:
            logger.i(f"Offsets guessed (IV: {iv_offset}, data: {data_offset}).")
            if iv_offset != def_iv_offset or data_offset != def_data_offset:
                logger.i(f"Next time, use -ivo {iv_offset} -do {data_offset} for guess-free decryption")
            break

    if data_offset == -1:
        return None

    iv = db_header[iv_offset : iv_offset + 16]  # noqa # type: ignore
    encrypted.seek(data_offset)
    file_hash.update(db_header[:data_offset])

    return AES.new(key, AES.MODE_GCM, iv)


# Main function
def main():
    print("-" * 48)
    print("Copyright © 2024 c4n6. All rights reserved")
    print("-" * 48)
    args = parsecmdline()
    logger = Log(verbose=args.verbose, force=args.force)

    if not (0 < args.data_offset < HEADER_SIZE - 128):
        logger.f(f"The data offset must be between 1 and {HEADER_SIZE - 129}")

    if not (0 < args.iv_offset < HEADER_SIZE - 128):
        logger.f(f"The IV offset must be between 1 and {HEADER_SIZE - 129}")

    if args.buffer_size is not None:
        if not 1 < args.buffer_size < io.DEFAULT_BUFFER_SIZE:
            logger.f("Invalid buffer size")

    key = Key(logger, args.key)
    logger.v(str(key))
    cipher = None
    file_hash = md5()

    if not args.no_protobuf:
        cipher = parse_protobuf(logger=logger, file_hash=file_hash, key=key, encrypted=args.ciphertext)

    if cipher is None and not args.no_guess:
        cipher = guess_offsets(
            logger=logger,
            file_hash=file_hash,
            key=key.key,
            encrypted=args.ciphertext,
            def_iv_offset=args.iv_offset,
            def_data_offset=args.data_offset,
        )

    if args.buffer_size is not None:
        decrypt(logger, file_hash, cipher, args.ciphertext, args.plaintext, args.buffer_size)
    elif args.no_mem:
        decrypt(logger, file_hash, cipher, args.ciphertext, args.plaintext, io.DEFAULT_BUFFER_SIZE)
    else:
        decrypt(logger, file_hash, cipher, args.ciphertext, args.plaintext)

    logger.i("Done")


if __name__ == "__main__":
    main()