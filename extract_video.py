import os
import json
from utils import extract_bytes_from_image, decrypt_file_stream
from PIL import Image

def extract_video(stego_folder, output_video, password="MyStrongPass123"):
    manifest_path = os.path.join(stego_folder, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError("❌ manifest.json not found in stego folder.")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    temp_encrypted = os.path.join(stego_folder, "temp_recovered.bin")
    with open(temp_encrypted, "wb") as f_out:
        for chunk in manifest["chunks"]:
            img_path = os.path.join(stego_folder, chunk["image"])
            data = extract_bytes_from_image(img_path, chunk["size"])
            f_out.write(data)

    if manifest["encrypted"]:
        print("[*] Decrypting recovered data...")
        salt = bytes.fromhex(manifest["salt"])
        iv = bytes.fromhex(manifest["iv"])
        decrypt_file_stream(temp_encrypted, output_video, password, salt, iv)
    else:
        os.rename(temp_encrypted, output_video)

    print(f"✅ Video recovered successfully → {output_video}")

if __name__ == "__main__":
    extract_video(
        stego_folder="stego_out",
        output_video="recovered_video.mp4",
        password="MyStrongPass123"
    )
