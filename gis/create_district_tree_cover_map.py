
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# --------------------------------------------------
# Paths
# --------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent

GPKG_PATH = ROOT / "data" / "processed" / "uttarakhand_districts.gpkg"

CSV_PATH = (
    ROOT / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "district_tree_cover_2021_v2.csv"
)

OUTPUT_DIR = (
    ROOT / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
)

OUTPUT_PATH = OUTPUT_DIR / "uttarakhand_district_tree_cover_percentage_2021.png"

# --------------------------------------------------
# Read data
# --------------------------------------------------
print("Reading district boundaries...")
districts = gpd.read_file(GPKG_PATH, layer="districts")

print("Reading tree-cover statistics...")
stats = pd.read_csv(CSV_PATH, dtype={"DIST_LGD": str})

# --------------------------------------------------
# Join using district LGD codes
# --------------------------------------------------
districts["DIST_LGD"] = districts["DIST_LGD"].astype(str).str.zfill(3)

merged = districts.merge(
    stats,
    on="DIST_LGD",
    how="left",
    validate="one_to_one"
)

if len(merged) != 13 or merged["Tree_Cover_Percent"].isna().any():
    raise ValueError("District data join failed or contains missing values.")

# --------------------------------------------------
# Plot map
# --------------------------------------------------
print("Creating choropleth map...")

fig, ax = plt.subplots(figsize=(12, 12))

cmap = plt.colormaps["YlGn"]
norm = Normalize(vmin=0, vmax=100)

merged.plot(
    column="Tree_Cover_Percent",
    cmap=cmap,
    norm=norm,
    linewidth=0.8,
    edgecolor="#333333",
    ax=ax
)

# District labels
for _, row in merged.iterrows():
    point = row.geometry.representative_point()

    label = (
        f"{row['DISTRICT_NAME']}\n"
        f"{row['Tree_Cover_Percent']:.1f}%"
    )

    ax.annotate(
        label,
        xy=(point.x, point.y),
        ha="center",
        va="center",
        fontsize=7,
        color="#17221a",
        fontweight="bold"
    )

# Colorbar
sm = ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])

cbar = fig.colorbar(
    sm,
    ax=ax,
    fraction=0.035,
    pad=0.025
)

cbar.set_label("Tree Cover (%)", fontsize=11)

# Title and layout
ax.set_title(
    "District-wise Tree Cover Percentage\n"
    "Uttarakhand | ESA WorldCover 2021",
    fontsize=15,
    fontweight="bold",
    pad=18
)

ax.set_axis_off()

fig.text(
    0.5,
    0.025,
    "Source: ESA WorldCover 2021 v200 | "
    "District boundaries: Survey of India",
    ha="center",
    fontsize=8
)

plt.tight_layout(rect=[0, 0.04, 1, 1])

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fig.savefig(
    OUTPUT_PATH,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.close(fig)

print("\nMAP CREATED SUCCESSFULLY")
print("Output:", OUTPUT_PATH)
print("Districts mapped:", len(merged))
print("Tree-cover percentage range:",
      f"{merged['Tree_Cover_Percent'].min():.2f}% - "
      f"{merged['Tree_Cover_Percent'].max():.2f}%")
print("Output size (KB):", round(OUTPUT_PATH.stat().st_size / 1024, 2))
