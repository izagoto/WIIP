import io
from hashlib import md5
from .logger import Log
from .key import Key
from .decryptor import decrypt, parse_protobuf, guess_offsets
from .utils import parsecmdline, HEADER_SIZE


def main():
    print("© 2024 4n6. All rights reserved.")
    args = parsecmdline()
    logger = Log(verbose=args.verbose, force=args.force)

    if not (0 < args.data_offset < HEADER_SIZE - 128):
        logger.f(f"The data offset must be between 1 and {HEADER_SIZE - 129}")

    if not (0 < args.iv_offset < HEADER_SIZE - 128):
        logger.f(f"The IV offset must be between 1 and {HEADER_SIZE - 129}")

    if args.buffer_size is not None:
        if not 1 < args.buffer_size < io.DEFAULT_BUFFER_SIZE:
            logger.f("Invalid buffer size")

    key = Key(logger, args.hexkey)
    logger.v(str(key))
    cipher = None
    file_hash = md5()

    if not args.no_protobuf:
        cipher = parse_protobuf(logger=logger, file_hash=file_hash, key=key, encrypted=args.encrypted)

    if cipher is None and not args.no_guess:
        cipher = guess_offsets(
            logger=logger,
            file_hash=file_hash,
            key=key.key,
            encrypted=args.encrypted,
            def_iv_offset=args.iv_offset,
            def_data_offset=args.data_offset,
        )

    if args.buffer_size is not None:
        decrypt(logger, file_hash, cipher, args.encrypted, args.decrypted, args.buffer_size)
    elif args.no_mem:
        decrypt(logger, file_hash, cipher, args.encrypted, args.decrypted, io.DEFAULT_BUFFER_SIZE)
    else:
        decrypt(logger, file_hash, cipher, args.encrypted, args.decrypted)

    logger.i("Done")


if __name__ == "__main__":
    main()