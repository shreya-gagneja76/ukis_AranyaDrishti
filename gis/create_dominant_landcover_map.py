
from pathlib import Path

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

BASE = Path(__file__).resolve().parent.parent

DATA_DIR = (
    BASE / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
)

CSV_FILE = DATA_DIR / "district_land_cover_composition_2021.csv"
GPKG_FILE = BASE / "data" / "processed" / "uttarakhand_districts.gpkg"

OUTPUT_FILE = DATA_DIR / "uttarakhand_dominant_landcover_2021.png"

# Read existing validated datasets.
df = pd.read_csv(CSV_FILE, dtype={"DIST_LGD": str})
districts = gpd.read_file(GPKG_FILE, layer="districts")

# Select the largest land-cover class in each district.
dominant = (
    df.sort_values(
        ["DIST_LGD", "Percent_of_District", "Class_Code"],
        ascending=[True, False, True]
    )
    .drop_duplicates(subset="DIST_LGD")
    [["DIST_LGD", "Land_Cover", "Percent_of_District"]]
)

# Join using unique district codes.
gdf = districts.merge(
    dominant,
    on="DIST_LGD",
    how="left",
    validate="one_to_one"
)

# Validate the joined result.
if len(gdf) != 13:
    raise ValueError(f"Expected 13 districts, found {len(gdf)}")

if gdf["Land_Cover"].isna().any():
    raise ValueError("Some districts have no dominant land-cover class.")

if gdf.geometry.isna().any() or (~gdf.geometry.is_valid).any():
    raise ValueError("Invalid or missing district geometry found.")

# Class colours.
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

gdf["Map_Color"] = gdf["Land_Cover"].map(colors)

if gdf["Map_Color"].isna().any():
    raise ValueError("A land-cover class has no assigned map colour.")

fig, ax = plt.subplots(figsize=(11, 12))

# Draw district polygons.
for land_cover, subset in gdf.groupby("Land_Cover"):
    subset.plot(
        ax=ax,
        color=colors[land_cover],
        edgecolor="#333333",
        linewidth=0.8
    )

# Add district labels.
for _, row in gdf.iterrows():
    point = row.geometry.representative_point()

    ax.annotate(
        row["DISTRICT_NAME"],
        (point.x, point.y),
        ha="center",
        va="center",
        fontsize=7,
        fontweight="bold"
    )

# Legend only includes classes present as dominant classes.
present_classes = sorted(gdf["Land_Cover"].unique())

legend_handles = [
    Patch(
        facecolor=colors[name],
        edgecolor="#333333",
        label=name
    )
    for name in present_classes
]

ax.legend(
    handles=legend_handles,
    title="Dominant land-cover class",
    loc="lower left",
    frameon=True,
    fontsize=9
)

ax.set_title(
    "Dominant Land-Cover Class by District\n"
    "Uttarakhand | ESA WorldCover 2021",
    fontsize=15,
    fontweight="bold",
    pad=16
)

ax.set_axis_off()

fig.text(
    0.5,
    0.025,
    "Dominant class = land-cover class with the largest share of district area\n"
    "Source: ESA WorldCover 2021 v200",
    ha="center",
    fontsize=9
)

plt.tight_layout(rect=[0, 0.06, 1, 0.97])

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

print("DOMINANT LAND-COVER MAP CREATED")
print("=" * 45)
print("Districts mapped:", len(gdf))
print("Dominant classes:", len(present_classes))
print("\nDISTRICT-WISE DOMINANT CLASS")

print(
    gdf[["DISTRICT_NAME", "Land_Cover", "Percent_of_District"]]
    .sort_values("DISTRICT_NAME")
    .to_string(index=False)
)

print("\nOutput:", OUTPUT_FILE)
print("Size (KB):", round(OUTPUT_FILE.stat().st_size / 1024, 2))
