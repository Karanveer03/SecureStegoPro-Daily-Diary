# utils.py
import os
import base64
from PIL import Image
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# ---------- Encryption (AES-CTR streaming) ----------
def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_file_stream(in_path: str, out_path: str, password: str):
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    iv = os.urandom(16)  # CTR nonce (IV)
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        while True:
            chunk = fin.read(64 * 1024)
            if not chunk:
                break
            fout.write(encryptor.update(chunk))
        fout.write(encryptor.finalize())
    return salt, iv

def decrypt_file_stream(in_path: str, out_path: str, password: str, salt: bytes, iv: bytes):
    key = _derive_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        while True:
            chunk = fin.read(64 * 1024)
            if not chunk:
                break
            fout.write(decryptor.update(chunk))
        fout.write(decryptor.finalize())

# ---------- Image capacity and LSB embed/extract ----------
def image_capacity_bytes(image_path: str) -> int:
    img = Image.open(image_path)
    w, h = img.size
    return (w * h * 3) // 8

def _bytes_to_bits_iter(data: bytes):
    for b in data:
        for i in range(8):
            yield (b >> (7 - i)) & 1

def embed_bytes_into_image(cover_path: str, data_bytes: bytes, out_path: str):
    img = Image.open(cover_path).convert("RGB")
    w, h = img.size
    capacity_bits = w * h * 3
    needed_bits = len(data_bytes) * 8
    if needed_bits > capacity_bits:
        raise ValueError(f"Data needs {needed_bits} bits but image has {capacity_bits} bits capacity.")
    pixels = list(img.getdata())
    bit_iter = _bytes_to_bits_iter(data_bytes)
    new_pixels = []
    for pix in pixels:
        r, g, b = pix
        new_rgb = []
        for c in (r, g, b):
            try:
                bit = next(bit_iter)
                new_c = (c & ~1) | bit
            except StopIteration:
                new_c = c
            new_rgb.append(new_c)
        new_pixels.append(tuple(new_rgb))
    new_img = Image.new("RGB", (w, h))
    new_img.putdata(new_pixels)
    new_img.save(out_path, "PNG")

def extract_bytes_from_image(stego_path: str, expected_bytes: int) -> bytes:
    img = Image.open(stego_path).convert("RGB")
    pixels = list(img.getdata())
    bits_needed = expected_bytes * 8
    bits = []
    for pix in pixels:
        for c in pix:
            bits.append(c & 1)
            if len(bits) >= bits_needed:
                out = bytearray()
                for i in range(0, bits_needed, 8):
                    byte = 0
                    for j in range(8):
                        byte = (byte << 1) | bits[i + j]
                    out.append(byte)
                return bytes(out)
    raise ValueError("Not enough data in stego image to extract expected bytes.")
