import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

cryptKey = bytes(
    [
        0x9C,
        0x93,
        0x5B,
        0x48,
        0x73,
        0x0A,
        0x55,
        0x4D,
        0x6B,
        0xFD,
        0x7C,
        0x63,
        0xC8,
        0x86,
        0xA9,
        0x2B,
        0xD3,
        0x90,
        0x19,
        0x8E,
        0xB8,
        0x12,
        0x8A,
        0xFB,
        0xF4,
        0xDE,
        0x16,
        0x2B,
        0x8B,
        0x95,
        0xF6,
        0x38,
    ]
)


def crypt(in_bytes, iv):
    cipher = AES.new(cryptKey, AES.MODE_CTR, nonce=b"", initial_value=iv)
    return cipher.encrypt(in_bytes)


def obscure(x):
    plaintext = x.encode("utf-8")
    iv = get_random_bytes(AES.block_size)
    ciphertext = crypt(plaintext, iv)
    return base64.urlsafe_b64encode(iv + ciphertext).decode("utf-8")


def reveal(x):
    data = base64.urlsafe_b64decode(x)
    iv, ciphertext = data[: AES.block_size], data[AES.block_size :]
    return crypt(ciphertext, iv).decode("utf-8")


if __name__ == "__main__":
    obscured = obscure("hello")
    print("Obscured:", obscured)

    revealed = reveal(obscured)
    print("Revealed:", revealed)
