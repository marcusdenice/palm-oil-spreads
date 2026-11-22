# ---------------------------------------------------------------------------
# FILTER ONE USDA BRANDED FOODS RELEASE
# Shrinks a raw release before upload to the Databricks bronze volume.
#   1. Keeps only rows in the project's categories (exact match)
#   2. Keeps only the columns the project needs
#   3. Saves both files as compressed CSVs (Databricks reads .gz directly)
# Every product in the chosen categories is kept, with no ingredient filter.
# Palm oil detection happens later, in the silver layer.
# Output:  data/filtered/release=<release>/branded_food.csv.gz
#          data/filtered/release=<release>/food.csv.gz
# Usage:   python filter_release.py
# Requires: pandas (pathlib and sys are built into Python)
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

import pandas as pd

# ---- Settings --------------------------------------------------------------
# Release label in YYYY-MM format, matching the Databricks volume folders
RELEASE_LABEL = "2026-10"

# Folder that contains this release's unzipped USDA CSV files
SOURCE_FOLDER = Path("FoodData_Central_branded_food_2026_10_29")

# Output folder, matching the volume layout: release=YYYY-MM
OUTPUT_FOLDER = Path("data") / "filtered" / f"release={RELEASE_LABEL}"

# Exact USDA category names to keep. Add more categories here to change scope of project.
# Older releases may use different names, so check them with
# profile_release.py first.
CATEGORIES_TO_KEEP = [
    "Nut & Seed Butters",
]

# Columns to keep from branded_food.csv
BRANDED_FOOD_COLUMNS = [
    "fdc_id",                 # USDA ID for this version of the product
    "brand_owner",            # Company that owns the brand
    "brand_name",             # Brand shown on the package (often blank)
    "subbrand_name",          # Product line within the brand, if any
    "gtin_upc",               # Barcode: links the same product across releases
    "ingredients",            # Full ingredient text from the label
    "branded_food_category",  # USDA's category for the product
    "data_source",            # Where USDA got the label data, such as GDSN
    "market_country",         # Country where the product is sold
    "modified_date",          # When the label data was last changed
    "available_date",         # When the record became available to USDA
    "discontinued_date",      # When the product was discontinued, if known
]

# Columns to keep from food.csv
FOOD_COLUMNS = [
    "fdc_id",            # Joins to branded_food.csv
    "data_type",         # Should be "branded_food" for every row
    "description",       # Product name
    "publication_date",  # When this version was published in FoodData Central
]

# Rows to read at a time. Reading in pieces keeps memory use low.
ROWS_PER_CHUNK = 200_000


# ---- Helper functions ------------------------------------------------------
def get_columns_that_exist(csv_path, wanted_columns):
    """
    Return only the wanted columns that appear in the file.
    Older releases may be missing some columns, so this prints a note
    instead of stopping with an error.
    """
    # nrows=0 reads only the header row, which is fast
    columns_in_file = pd.read_csv(csv_path, nrows=0).columns

    missing = [col for col in wanted_columns if col not in columns_in_file]
    if missing:
        print(f"Note: {csv_path.name} is missing: {missing}")

    return [col for col in wanted_columns if col in columns_in_file]


def read_in_chunks(csv_path, columns):
    """
    Read a large CSV in pieces, keeping only the chosen columns.
    dtype=str keeps values exactly as written, so barcodes keep
    their leading zeros.
    """
    return pd.read_csv(csv_path, dtype=str, usecols=columns,
                       chunksize=ROWS_PER_CHUNK)


# ---- 1. Check that the source files exist ----------------------------------
for file_name in ["branded_food.csv", "food.csv"]:
    if not (SOURCE_FOLDER / file_name).exists():
        sys.exit(f"Error: {file_name} not found in {SOURCE_FOLDER}")

print(f"Release:    {RELEASE_LABEL}")
print(f"Source:     {SOURCE_FOLDER}")
print(f"Categories: {CATEGORIES_TO_KEEP}")


# ---- 2. Filter branded_food.csv to the project's categories ----------------
print("\nFiltering branded_food.csv (this can take a few minutes)...")
branded_path = SOURCE_FOLDER / "branded_food.csv"
branded_columns = get_columns_that_exist(branded_path, BRANDED_FOOD_COLUMNS)

branded_pieces = []
for chunk in read_in_chunks(branded_path, branded_columns):
    # True for rows whose category is in CATEGORIES_TO_KEEP
    is_project_category = chunk["branded_food_category"].isin(CATEGORIES_TO_KEEP)
    branded_pieces.append(chunk[is_project_category])

# Stack the matching pieces into one table
branded_food = pd.concat(branded_pieces, ignore_index=True)

# Stop if nothing matched, which usually means a category name is spelled
# differently in this release
if branded_food.empty:
    sys.exit("Error: no rows matched CATEGORIES_TO_KEEP. "
             "Check the category names with profile_release.py.")


# ---- 3. Filter food.csv to the same products -------------------------------
print("Filtering food.csv...")
food_path = SOURCE_FOLDER / "food.csv"
food_columns = get_columns_that_exist(food_path, FOOD_COLUMNS)

# Products kept in step 2. food.csv joins to branded_food.csv on fdc_id.
product_ids_to_keep = set(branded_food["fdc_id"])

food_pieces = []
for chunk in read_in_chunks(food_path, food_columns):
    is_kept_product = chunk["fdc_id"].isin(product_ids_to_keep)
    food_pieces.append(chunk[is_kept_product])

food = pd.concat(food_pieces, ignore_index=True)


# ---- 4. Save both files as compressed CSVs ---------------------------------
# index=False stops pandas from adding an extra row-number column
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
branded_food.to_csv(OUTPUT_FOLDER / "branded_food.csv.gz",
                    index=False, compression="gzip")
food.to_csv(OUTPUT_FOLDER / "food.csv.gz",
            index=False, compression="gzip")


# ---- 5. Summary ------------------------------------------------------------
print("\n" + "-" * 60)
print("OUTPUT FILES")
print("-" * 60)
for file in sorted(OUTPUT_FOLDER.iterdir()):
    size_mb = file.stat().st_size / 1_000_000
    print(f"{file.name:<25} {size_mb:.2f} MB")

print("\n" + "-" * 60)
print("ROWS KEPT")
print("-" * 60)
print(f"branded_food: {len(branded_food):,}")
print(f"food:         {len(food):,}")

# These two counts should match. A difference means some products
# exist in one file but not the other.
if len(branded_food) != len(food):
    print("Note: row counts differ between the two files. Check in profiling.")

print("\n" + "-" * 60)
print("ROWS PER CATEGORY")
print("-" * 60)
print(branded_food["branded_food_category"].value_counts().to_string())

print(f"\nDone. Upload both files to:")
print(f"/Volumes/palm/bronze/raw_files/usda_branded/release={RELEASE_LABEL}/")