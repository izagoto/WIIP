import zlib
from re import findall
from Cryptodome.Cipher import AES
from google.protobuf.message import DecodeError
import io

from .utils import test_decompression, oscillate, HEADER_SIZE


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

                try:
                    output_decrypted = cipher.decrypt(encrypted_data)
                except ValueError as e:
                    logger.f(f"Decryption failed: {e}. Backup corrupted.")

                try:
                    if is_multifile_backup:
                        output_decrypted += cipher.decrypt(authentication_tag)  # type: ignore
                        cipher.verify(checksum)
                    else:
                        cipher.verify(authentication_tag)
                except ValueError as e:
                    logger.e(f"Tag mismatch: {e}. Backup corrupted.")

                try:
                    output_file = z_obj.decompress(output_decrypted)  # type: ignore
                    if not z_obj.eof:
                        logger.e("Database truncated.")
                except zlib.error:
                    output_file = output_decrypted  # type: ignore

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
                    if len(chunk) < buffer_size:  # type: ignore
                        logger.f("Buffer size too large. Use smaller buffer.")
                    continue
                try:
                    next_chunk = encrypted.read(buffer_size)
                except MemoryError:
                    logger.f("Out of RAM. Use smaller buffer size.")

                if next_chunk is None:
                    continue

                next_chunk_len = len(next_chunk)
                if next_chunk_len <= 36:
                    if next_chunk_len == 36:
                        checksum = next_chunk
                    elif next_chunk_len == 0:
                        checksum = chunk[-36:]
                        chunk = chunk[:-36]
                    else:
                        checksum = chunk[-(36 - next_chunk_len) :] + next_chunk
                        chunk = chunk[: -(36 - next_chunk_len)]

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
    try:
        import proto.prefix_pb2 as prefix
    except ImportError as e:
        logger.e(f"Import error: {e}")
        return None
    except AttributeError as e:
        logger.e(f"Proto classes error: {e}. Update protobuf to 3.20.0+.")
        return None

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

    if data_offset is None or data_offset == -1 or iv_offset is None or db_header is None:
        return None

    iv = db_header[iv_offset : iv_offset + 16]  # noqa
    encrypted.seek(data_offset)
    file_hash.update(db_header[:data_offset])

    return AES.new(key, AES.MODE_GCM, iv)