#!/usr/bin/python3
import os
from pathlib import Path
import subprocess
import urllib.request
import sys

# -----------------------------
# Paths
# -----------------------------
home = Path.home()
steam_common = home / ".steam/steam/steamapps/common"
steam_root = home / ".steam/steam"

# -----------------------------
# Check Steam
# -----------------------------
if not steam_common.exists():
	print("Steam common folder not found!")
	exit(1)

# -----------------------------
# Find Proton installs
# -----------------------------
protons = []

for folder in steam_common.iterdir():
	if folder.is_dir() and (folder / "proton").exists():
		protons.append(folder)

if not protons:
	print("No Proton installations found!")
	exit(1)

protons.sort(key=lambda p: ("experimental" not in p.name.lower(), p.name))

# -----------------------------
# Select Proton
# -----------------------------
print("Select Proton Version:")
print("Proton Experimental is recommended.\n")

for i, proton in enumerate(protons, 1):
	print(f"{i}. {proton.name}")

while True:
	try:
		idx = int(input("> ")) - 1
		if 0 <= idx < len(protons):
			break
		print("Invalid index!")
	except ValueError:
		print("Input must be a number!")

proton = protons[idx]
proton_exec = proton / "proton"

print(f"Using Proton: {proton.name}")

# -----------------------------
# Choose prefix
# -----------------------------
choice = input("Create a WINEPREFIX for Aisaka? [y/N] > ").strip().lower()

compat_base = home / ".steam/steam/steamapps/compatdata"

if choice in ("y", "yes"):
	steam_compatdata = compat_base / "aisaka"
	print("Will create dedicated prefix.")
else:
	steam_compatdata = compat_base / "0"
	print("Using default prefix (0).")

steam_compatdata.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Proton environment
# -----------------------------
env = os.environ.copy()
env["STEAM_COMPAT_DATA_PATH"] = str(steam_compatdata)
env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_root)

# -----------------------------
# Init prefix
# -----------------------------
print("Initializing Proton prefix...")

subprocess.run([
	str(proton_exec),
	"run",
	"wineboot"
], env=env)

# -----------------------------
# Downloader
# -----------------------------
def download_file(url, dest):
	with urllib.request.urlopen(url) as response:
		total = response.getheader("Content-Length")
		total = int(total) if total else None

		chunk_size = 8192
		downloaded = 0

		with open(dest, "wb") as f:
			while True:
				chunk = response.read(chunk_size)
				if not chunk:
					break

				f.write(chunk)
				downloaded += len(chunk)

				if total:
					percent = int(downloaded * 100 / total)
					bar = "#" * (percent // 2)
					sys.stdout.write(f"\r[{bar:<50}] {percent}%")
				else:
					sys.stdout.write(f"\rDownloaded {downloaded} bytes")

				sys.stdout.flush()

	print()

# -----------------------------
# Download Aisaka
# -----------------------------
aisaka_url = "https://github.com/caelusinfra/game-launcher/releases/latest/download/AisakaLauncher.exe"

install_dir = steam_compatdata / "pfx/drive_c/Program Files/Aisaka"
install_dir.mkdir(parents=True, exist_ok=True)

exe_path = install_dir / "AisakaLauncher.exe"

print("Downloading Aisaka...")
download_file(aisaka_url, exe_path)

# -----------------------------
# Launch test (optional)
# -----------------------------
print("Launching Aisaka...")

subprocess.run([
	str(proton_exec),
	"run",
	str(exe_path)
], env=env)

# -----------------------------
# Create launcher script
# -----------------------------
bin_path = home / ".local/bin"
bin_path.mkdir(parents=True, exist_ok=True)

launcher_path = bin_path / "aisaka-launcher"

launcher_script = f"""#!/bin/bash
export STEAM_COMPAT_DATA_PATH="{steam_compatdata}"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="{steam_root}"
PROTON="{proton_exec}"
"$PROTON" run "$STEAM_COMPAT_DATA_PATH/pfx/drive_c/Program Files/Aisaka/AisakaLauncher.exe" "$@"
"""

with open(launcher_path, "w") as f:
	f.write(launcher_script)

os.chmod(launcher_path, 0o755)

# -----------------------------
# Create desktop entry
# -----------------------------
app_path = home / ".local/share/applications"
app_path.mkdir(parents=True, exist_ok=True)

desktop_path = app_path / "aisaka.desktop"

desktop_file = f"""[Desktop Entry]
Name=Aisaka
Exec={launcher_path} %u
Type=Application
Terminal=false
MimeType=x-scheme-handler/aisaka-launcher;
"""

with open(desktop_path, "w") as f:
	f.write(desktop_file)

# -----------------------------
# Register MIME handler
# -----------------------------
subprocess.run([
	"xdg-mime",
	"default",
	"aisaka.desktop",
	"x-scheme-handler/aisaka-launcher"
])

# -----------------------------
# Update desktop DB
# -----------------------------
subprocess.run([
	"update-desktop-database",
	str(app_path)
])

print("\nDone! Aisaka is installed and registered")
