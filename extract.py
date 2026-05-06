# extract.py
import os
import json
import argparse
import base64
from utils import extract_bytes_from_image, decrypt_file_stream

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True, help="Path to manifest.json created by embed.py")
    p.add_argument("--stego_folder", required=False, help="Folder where stego images live (optional)")
    p.add_argument("--output", required=True, help="Output recovered filename")
    p.add_argument("--password", default=None, help="Password if the original was encrypted")
    args = p.parse_args()

    with open(args.manifest, "r") as f:
        manifest = json.load(f)

    base = args.stego_folder if args.stego_folder else os.path.dirname(args.manifest)
    temp_combined = os.path.join(base, "recovered_combined.temp")

    with open(temp_combined, "wb") as fout:
        for chunk in manifest["chunks"]:
            stego_file = chunk["stego_file"]
            stego_path = os.path.join(base, stego_file)
            data = extract_bytes_from_image(stego_path, chunk["chunk_size"])
            fout.write(data)

    if manifest.get("encrypted", False):
        if not args.password:
            raise SystemExit("Manifest indicates file was encrypted. Provide --password.")
        salt = base64.b64decode(manifest["salt"])
        iv = base64.b64decode(manifest["iv"])
        decrypt_file_stream(temp_combined, args.output, args.password, salt, iv)
        os.remove(temp_combined)
    else:
        os.replace(temp_combined, args.output)

    print("Extraction complete. Recovered file:", args.output)

if __name__ == "__main__":
    main()
