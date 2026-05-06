from PIL import Image
import os

def image_capacity_bytes(img_path):
    with Image.open(img_path) as img:
        w, h = img.size
        return (w * h * 3) // 8

folder = "covers"
total = 0
for f in os.listdir(folder):
    if f.lower().endswith(".png"):
        total += image_capacity_bytes(os.path.join(folder, f))

print(f"Total cover capacity: {total/1024/1024:.2f} MB")
