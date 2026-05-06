# test_setup.py
from PIL import Image
from cryptography.fernet import Fernet
from tqdm import tqdm
import time

def main():
    print("✅ All libraries imported successfully!\n")

    # Create a tiny 100x100 image to test Pillow
    img = Image.new("RGB", (100, 100), color="orange")
    img.save("test_image.png")
    print("🖼️  Created test_image.png\n")

    # Test encryption
    key = Fernet.generate_key()
    cipher = Fernet(key)
    message = b"Hello SecureStego!"
    token = cipher.encrypt(message)
    decrypted = cipher.decrypt(token)
    print(f"🔐 Encryption test passed: {decrypted.decode()}\n")

    # Test tqdm progress bar
    print("⏳ Progress bar test:")
    for _ in tqdm(range(30)):
        time.sleep(0.05)

    print("\n✅ Environment test complete! You are ready to run embed.py 🚀")

if __name__ == "__main__":
    main()
