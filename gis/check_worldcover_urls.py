
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

tiles = [
    "N27E075",
    "N27E078",
    "N30E075",
    "N30E078",
    "N30E081",
]

base_url = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
    "v200/2021/map/"
)

for tile in tiles:
    filename = (
        f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    )
    url = base_url + filename

    print(f"\nChecking {tile}...")

    request = Request(url, method="HEAD")

    try:
        with urlopen(request, timeout=30) as response:
            size_mb = int(response.headers.get("Content-Length", 0)) / (1024 * 1024)

            print("HTTP status:", response.status)
            print(f"File size: {size_mb:.2f} MB")
            print("URL:", url)

    except (HTTPError, URLError, TimeoutError) as error:
        print("Could not verify:", error)
