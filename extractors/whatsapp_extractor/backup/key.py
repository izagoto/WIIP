import hmac
from hashlib import sha256
import javaobj.v2 as javaobj
from .utils import from_hex, javaintlist2bytes


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
        self.key = None
        self.serversalt = None
        self.key_version = None
        self.cipher_version = None

        hexkey = b""

        logger.v("Reading hexkey...")

        try:
            key_file_stream = open(key_file_name, "rb")
            try:
                jarr = javaobj.load(key_file_stream).data  # type: ignore
                hexkey = javaintlist2bytes(jarr)
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