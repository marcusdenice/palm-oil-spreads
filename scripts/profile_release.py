# ---------------------------------------------------------------------------
# PROFILE ONE USDA BRANDED FOODS RELEASE
# First look at a raw release before filtering or loading to Databricks.
#   1. Prints the column names in branded_food.csv
#   2. Prints the first row, so you can see what real values look like
#   3. Saves every category with its row count to a CSV for review
# Output:  data_exploration/<release>/categories.csv
# Usage:   python profile_release.py
# Requires: pandas (pathlib is built into Python)
# ---------------------------------------------------------------------------
from pathlib import Path

import pandas as pd

# ---- Settings --------------------------------------------------------------
# Release label in YYYY-MM format, matching the Databricks volume folders
RELEASE_LABEL = "2026-10"

# Path to the full, unfiltered branded_food.csv for this release
CSV_PATH = Path("FoodData_Central_branded_food_2026_10_29") / "branded_food.csv"

# Folder for this release's exploration output
OUTPUT_FOLDER = Path("data_exploration") / RELEASE_LABEL

# Label shown for products that have no category
NO_CATEGORY_LABEL = "No Listed Category"


# ---- 1. Column names -------------------------------------------------------
# Read only the first row. dtype=str keeps values exactly as written,
# so barcodes keep their leading zeros.
first_row = pd.read_csv(CSV_PATH, nrows=1, dtype=str)

print("-" * 60)
print(f"COLUMNS ({len(first_row.columns)})")
print("-" * 60)
for number, column in enumerate(first_row.columns, start=1):
    print(f"{number:>2}. {column}")
print("-" * 60)


# ---- 2. First row ----------------------------------------------------------
# Print each column next to its value, one per line,
# so long text such as ingredients is easy to read.
print("-" * 60)
print("FIRST ROW")
print("-" * 60)
for column, value in first_row.iloc[0].items():
    print(f"{column:<30} {value}")


# ---- 3. Categories with row counts -----------------------------------------
# Read only the category column, which is much faster than loading the whole file.
categories = pd.read_csv(CSV_PATH, usecols=["branded_food_category"], dtype=str)

# Count rows per category, then sort alphabetically.
# dropna=False keeps blank categories, and na_position="first" puts them
# at the top of the list.
category_counts = (
    categories["branded_food_category"]
    .value_counts(dropna=False)
    .rename_axis("branded_food_category")
    .reset_index(name="row_count")
    .sort_values("branded_food_category", na_position="first")
)

# Replace blank categories with a readable label.
# This is done after sorting, so the label stays at the top.
category_counts["branded_food_category"] = (
    category_counts["branded_food_category"].fillna(NO_CATEGORY_LABEL)
)

# Empty column to fill in by hand, flagging the categories to include in
# the project. Open the CSV in a spreadsheet tool to review and complete it.
# Leave it blank for categories that aren't part of the project.
category_counts["include_in_project"] = ""

# Put the columns in the order they should appear in the CSV
category_counts = category_counts[
    ["row_count", "include_in_project", "branded_food_category"]
]


# ---- 4. Save the category list ---------------------------------------------
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
output_file = OUTPUT_FOLDER / "categories.csv"
category_counts.to_csv(output_file, index=False)

print(f"\nCATEGORIES: {len(category_counts):,} found")
print(f"Saved to {output_file}")