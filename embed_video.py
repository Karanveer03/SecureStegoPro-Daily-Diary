import os
import json
from tqdm import tqdm
from utils import image_capacity_bytes, embed_bytes_into_image, encrypt_file_stream

def embed_video(input_video, cover_folder, output_folder, encrypt=True, password="MyStrongPass123"):
    os.makedirs(output_folder, exist_ok=True)
    cover_images = sorted([os.path.join(cover_folder, f)
                           for f in os.listdir(cover_folder)
                           if f.lower().endswith(".png")])

    if not cover_images:
        raise ValueError("❌ No PNG images found in covers folder.")

    # Encrypt video first (file → encrypted temp)
    encrypted_path = os.path.join(output_folder, "temp_encrypted.bin")
    if encrypt:
        print("[*] Encrypting video file...")
        salt, iv = encrypt_file_stream(input_video, encrypted_path, password)
    else:
        with open(input_video, "rb") as f_in, open(encrypted_path, "wb") as f_out:
            f_out.write(f_in.read())
        salt, iv = b"", b""

    total_size = os.path.getsize(encrypted_path)
    print(f"[*] Encrypted file size: {total_size / (1024*1024):.2f} MB")

    manifest = {"file_name": os.path.basename(input_video),
                "encrypted": encrypt,
                "salt": salt.hex(),
                "iv": iv.hex(),
                "chunks": []}

    # Split encrypted file into image chunks
    with open(encrypted_path, "rb") as f:
        remaining = total_size
        chunk_index = 0
        for cover_path in tqdm(cover_images, desc="Embedding"):
            cap = image_capacity_bytes(cover_path)
            data = f.read(cap)
            if not data:
                break
            out_img = os.path.join(output_folder, f"stego_{chunk_index+1:03d}.png")
            embed_bytes_into_image(cover_path, data, out_img)
            manifest["chunks"].append({"image": os.path.basename(out_img), "size": len(data)})
            chunk_index += 1
            remaining -= len(data)
            if remaining <= 0:
                break

    with open(os.path.join(output_folder, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✅ Embedding complete. {chunk_index} images used.")
    print(f"Manifest saved → {output_folder}/manifest.json")

if __name__ == "__main__":
    embed_video(
        input_video="video.mp4",
        cover_folder="covers",
        output_folder="stego_out",
        encrypt=True,
        password="MyStrongPass123"
    )
