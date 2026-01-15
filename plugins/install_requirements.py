import subprocess
import sys

def install_packages():
    """Install all required packages"""
    packages = [
        "pyrogram==2.0.80",
        "TgCrypto",
        "motor",
        "dnspython",
        "hachoir",
        "Pillow",
        "aiohttp",
        "pytz",
        "humanize",
        "pyromod",
        "ffmpeg-python",
        "cloudscraper",
        "requests[socks]"
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
    
    # Try to install libtorrent (may require system dependencies)
    try:
        print("Installing libtorrent...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "libtorrent==2.0.9"])
        print("✓ libtorrent installed successfully")
    except:
        print("⚠ libtorrent installation may require system dependencies")
        print("You may need to run: sudo apt-get install python3-libtorrent")

if __name__ == "__main__":
    install_packages()
    print("\n✅ All packages installed! You can now run the bot.")
