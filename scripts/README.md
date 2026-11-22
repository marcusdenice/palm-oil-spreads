# Local Scripts

These scripts run on your own computer, **before** any data is uploaded to
Databricks. USDA's Branded Foods releases are about 3 GB each, so the files
are explored and shrunk locally first.

| Step | Script | Purpose | Output |
|---|---|---|---|
| 1 | `profile_release.py` | First look at a raw release: columns, a sample row, and categories | `data_exploration/<release>/categories.csv` |
| 2 | `filter_release.py` | Shrinks a release to the project's categories and columns before upload | `data/filtered/release=<release>/*.csv.gz` |
---

## profile_release.py

### What it does
1. Prints the column names in `branded_food.csv`
2. Prints the first row, so you can see what real values look like
3. Counts the rows in every food category and saves the list to a CSV

Products with no category are listed as **No Listed Category** at the top of
the file.

### Requirements
- Python 3.10 or later
- pandas:
  ```
  python -m pip install pandas
  ```

### Setup
1. Download a **Branded Foods CSV** release from the
   [USDA FoodData Central download page](https://fdc.nal.usda.gov/download-datasets).
2. Unzip it into the same folder as this script. The CSV files must sit
   directly inside the unzipped folder.
3. Update the settings at the top of the script:

| Setting | Meaning | Example |
|---|---|---|
| `RELEASE_LABEL` | Release in YYYY-MM format, matching the Databricks volume folder | `2026-10` |
| `CSV_PATH` | Path to that release's `branded_food.csv` | `FoodData_Central_branded_food_2026_10_29/branded_food.csv` |
| `NO_CATEGORY_LABEL` | Label for products with no category | `No Listed Category` |

### How to run (Windows)
1. Open the script's folder in File Explorer.
2. Type `cmd` in the address bar and press Enter.
3. Run:
   ```
   python profile_release.py
   ```

### Output
`data_exploration/<release>/categories.csv`, with three columns:

| Column | Meaning |
|---|---|
| `row_count` | Number of product rows in the category |
| `include_in_project` | Left blank by the script. Fill in by hand to mark categories for the project |
| `branded_food_category` | USDA's category name |

### Next step
Open `categories.csv` in a spreadsheet tool and mark the categories to include
in the project. The marked list becomes the category mapping seed in `seeds/`.

### Notes
- Every value is read as text, so barcodes keep their leading zeros.
- Only the category column is read for the counts, which keeps the run fast
  on a 3 GB file.
- Raw USDA files are **not** stored in this repo. Download them from USDA.
  
---

## filter_release.py

### What it does
1. Keeps only rows in the project's categories, using an exact name match
2. Keeps only the columns the project needs
3. Saves `branded_food.csv.gz` and `food.csv.gz`, compressed for upload

Every product in the chosen categories is kept. There is **no ingredient
filter**: palm oil detection happens later, in the silver layer, so the
project can measure the share of products with palm oil and see products
that removed it.

### Before you run it
Run `profile_release.py` on the same release first, and check that the names
in `CATEGORIES_TO_KEEP` appear in its `categories.csv`. Older releases may
use different category names.

### Settings
| Setting | Meaning | Example |
|---|---|---|
| `RELEASE_LABEL` | Release in YYYY-MM format, matching the Databricks volume folder | `2026-10` |
| `SOURCE_FOLDER` | Folder containing the unzipped USDA CSVs | `FoodData_Central_branded_food_2026_10_29` |
| `CATEGORIES_TO_KEEP` | Exact USDA category names to keep | `["Nut & Seed Butters"]` |
| `BRANDED_FOOD_COLUMNS` | Columns kept from `branded_food.csv` | See the script |
| `FOOD_COLUMNS` | Columns kept from `food.csv` | See the script |

### How to run (Windows)
1. Open the script's folder in File Explorer.
2. Type `cmd` in the address bar and press Enter.
3. Run:
   ```
   python filter_release.py
   ```

### Output
```
data/filtered/release=<release>/
├── branded_food.csv.gz
└── food.csv.gz
```

Upload both files to:
```
/Volumes/palm/bronze/raw_files/usda_branded/release=<release>/
```

### Checks built into the script
- Stops if either source CSV is missing
- Stops if no rows match `CATEGORIES_TO_KEEP`, which usually means a
  category name is spelled differently in that release
- Warns if the two output files have different row counts

### Notes
- Every value is read as text, so barcodes keep their leading zeros.
- Files are read in chunks of 200,000 rows to keep memory use low.
- Filtering before upload is a deliberate tradeoff: bronze holds a subset of
  USDA's data, not a full copy. To widen the scope, add categories and rerun.
- The `data/` folder is not stored in this repo.

