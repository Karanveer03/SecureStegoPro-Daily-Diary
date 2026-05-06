# embed.py
import os
import json
import argparse
import base64
from utils import image_capacity_bytes, encrypt_file_stream, embed_bytes_into_image
from tqdm import tqdm

def find_cover_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return files

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="File to hide (path)")
    p.add_argument("--cover", required=True, help="Folder with cover images (PNG recommended)")
    p.add_argument("--output", required=True, help="Output folder for stego images + manifest")
    p.add_argument("--encrypt", choices=("yes", "no"), default="no")
    p.add_argument("--password", default=None, help="Password for encryption (if encrypt=yes)")
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)
    covers = find_cover_images(args.cover)
    if not covers:
        raise SystemExit("No cover images found in folder. Use PNG images (lossless).")

    capacities = [image_capacity_bytes(c) for c in covers]
    total_capacity = sum(capacities)

    file_to_embed = args.input
    enc_meta = {}
    if args.encrypt == "yes":
        if not args.password:
            raise SystemExit("Encryption requested but no --password provided.")
        temp_enc = os.path.join(args.output, "encrypted.temp")
        salt, iv = encrypt_file_stream(args.input, temp_enc, args.password)
        file_to_embed = temp_enc
        enc_meta = {"encrypted": True,
                    "salt": base64.b64encode(salt).decode(),
                    "iv": base64.b64encode(iv).decode(),
                    "algorithm": "AES-CTR-256"}
    else:
        enc_meta = {"encrypted": False}

    file_size = os.path.getsize(file_to_embed)
    if total_capacity < file_size:
        raise SystemExit(f"Total cover capacity {total_capacity} bytes < file size {file_size} bytes.")

    manifest = {
        "original_filename": os.path.basename(args.input),
        "original_size": os.path.getsize(args.input),
        **enc_meta,
        "chunks": []
    }

    with open(file_to_embed, "rb") as fin:
        for idx, cover in enumerate(tqdm(covers, desc="Embedding")):
            capacity = capacities[idx]
            chunk = fin.read(capacity)
            if not chunk:
                break
            out_name = f"stego_{idx+1:03d}.png"
            out_path = os.path.join(args.output, out_name)
            embed_bytes_into_image(cover, chunk, out_path)
            manifest["chunks"].append({
                "stego_file": out_name,
                "cover_file": os.path.basename(cover),
                "chunk_size": len(chunk)
            })

    manifest_path = os.path.join(args.output, "manifest.json")
    with open(manifest_path, "w") as mf:
        json.dump(manifest, mf, indent=2)

    if args.encrypt == "yes" and os.path.exists(temp_enc):
        os.remove(temp_enc)

    print("Embedding complete. Manifest:", manifest_path)

if __name__ == "__main__":
    main()
