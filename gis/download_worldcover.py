
from pathlib import Path
from urllib.request import Request, urlopen
import shutil
import os

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "map"
)

BASE_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
    "v200/2021/map/"
)

TILES = [
    "N27E075",
    "N27E078",
    "N30E075",
    "N30E078",
    "N30E081",
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# First, check the size of all five files.
files = []

print("Checking download requirements...")

for tile in TILES:
    filename = (
        f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    )

    url = BASE_URL + filename
    request = Request(url, method="HEAD")

    with urlopen(request, timeout=30) as response:
        size = int(response.headers["Content-Length"])

    files.append((filename, url, size))

total_size = sum(size for _, _, size in files)
free_space = shutil.disk_usage(OUTPUT_DIR).free

print(f"Expected download: {total_size / (1024**2):.2f} MB")
print(f"Available disk space: {free_space / (1024**3):.2f} GB")

if free_space < total_size + 100 * 1024 * 1024:
    raise RuntimeError("Not enough free disk space.")

# Download each tile.
for filename, url, expected_size in files:

    destination = OUTPUT_DIR / filename
    temporary = OUTPUT_DIR / (filename + ".part")

    if destination.exists() and destination.stat().st_size == expected_size:
        print(f"\nAlready downloaded: {filename}")
        continue

    if temporary.exists():
        temporary.unlink()

    print(f"\nDownloading: {filename}")

    try:
        request = Request(url)

        with urlopen(request, timeout=60) as response:
            downloaded = 0

            with open(temporary, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    output.write(chunk)
                    downloaded += len(chunk)

                    percent = downloaded * 100 / expected_size

                    print(
                        f"\rProgress: {percent:.1f}%",
                        end="",
                        flush=True
                    )

        if temporary.stat().st_size != expected_size:
            raise RuntimeError("Downloaded file size mismatch.")

        os.replace(temporary, destination)

        print(f"\nCompleted: {filename}")

    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

print("\nAll five WorldCover tiles downloaded successfully!")
print("Location:", OUTPUT_DIR)
