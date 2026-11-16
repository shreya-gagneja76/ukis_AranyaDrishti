
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "district_land_cover_composition_2021.csv"
)

OUTPUT_FILE = (
    BASE / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "district_landcover_composition_2021.png"
)

df = pd.read_csv(INPUT_FILE)

# Pivot percentages into one row per district.
pivot = df.pivot(
    index="District",
    columns="Land_Cover",
    values="Percent_of_District"
)

# Remove classes with zero area throughout Uttarakhand.
pivot = pivot.loc[:, pivot.sum(axis=0) > 0]

# Order districts by tree-cover percentage.
pivot = pivot.sort_values(
    "Tree cover",
    ascending=False
)

# Check composition totals.
if not ((pivot.sum(axis=1) - 100).abs() < 0.01).all():
    raise ValueError("District percentages do not sum to 100%.")

colors = {
    "Tree cover": "#287A3E",
    "Shrubland": "#A5C85A",
    "Grassland": "#D5E68A",
    "Cropland": "#E5B84B",
    "Built-up": "#C85A50",
    "Bare / sparse vegetation": "#C5A477",
    "Snow and ice": "#E8EEF3",
    "Permanent water bodies": "#4287C5",
    "Herbaceous wetland": "#65B9B0",
    "Moss and lichen": "#8A9B50",
}

fig, ax = plt.subplots(figsize=(15, 9))

left = [0.0] * len(pivot)

for land_cover in pivot.columns:

    values = pivot[land_cover].values

    ax.barh(
        pivot.index,
        values,
        left=left,
        label=land_cover,
        color=colors.get(land_cover, "#888888"),
        edgecolor="white",
        linewidth=0.3
    )

    left = [
        previous + current
        for previous, current in zip(left, values)
    ]

ax.set_xlim(0, 100)
ax.invert_yaxis()

ax.set_xlabel("Share of district area (%)", fontsize=11)

ax.set_title(
    "Land-Cover Composition by District\n"
    "Uttarakhand | ESA WorldCover 2021",
    fontsize=15,
    fontweight="bold",
    pad=18
)

ax.grid(
    axis="x",
    linestyle="--",
    alpha=0.3
)

ax.set_axisbelow(True)

ax.legend(
    title="Land-cover class",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    frameon=False
)

fig.text(
    0.5,
    0.02,
    "Source: ESA WorldCover 2021 v200",
    ha="center",
    fontsize=9
)

plt.tight_layout(rect=[0, 0.04, 0.82, 1])

if OUTPUT_FILE.exists():
    raise FileExistsError(
        f"Output already exists; inspect it before replacing: {OUTPUT_FILE}"
    )

fig.savefig(
    OUTPUT_FILE,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.close(fig)

print("CHART CREATED SUCCESSFULLY")
print("Districts:", len(pivot))
print("Land-cover classes plotted:", len(pivot.columns))
print("Output:", OUTPUT_FILE)
print("Size (KB):", round(OUTPUT_FILE.stat().st_size / 1024, 2))
