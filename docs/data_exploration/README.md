## 2026-10 release review
**Run on:** 2026-11-21
**Source:** FoodData_Central_branded_food_2026_10_29/branded_food.csv
**Script:** `scripts/profile_release.py`
**Output:** `2026-10/categories.csv`

### Columns (21 total)
| # | Column | 
|---|---|
| 1 | fdc_id |
| 2 | brand_owner |
| 3 | brand_name |
| 4 | subbrand_name |
| 5 | gtin_upc |
| 6 | ingredients |
| 7 | not_a_significant_source_of |
| 8 | serving_size |
| 9 | serving_size_unit |
| 10 | household_serving_fulltext |
| 11 | branded_food_category |
| 12 | data_source |
| 13 | package_weight |
| 14 | modified_date |
| 15 | available_date |
| 16 | market_country |
| 17 | discontinued_date |
| 18 | preparation_state_code |
| 19 | trade_channel |
| 20 | short_description |
| 21 | material_code |

### Sample row
`nan` means the value is blank in the source file.

| Column | Value |
|---|---|
| fdc_id | 1105904 |
| brand_owner | Richardson Oilseed Products (US) Limited |
| brand_name | nan |
| subbrand_name | nan |
| gtin_upc | 00027000612323 |
| ingredients | Vegetable Oil |
| not_a_significant_source_of | nan |
| serving_size | 15.0 |
| serving_size_unit | ml |
| household_serving_fulltext | 1 Tbsp (15 ml) |
| branded_food_category | Oils Edible |
| data_source | GDSN |
| package_weight | nan |
| modified_date | 2020-10-02 |
| available_date | 2020-11-13 |
| market_country | United States |
| discontinued_date | nan |
| preparation_state_code | nan |
| trade_channel | nan |
| short_description | nan |
| material_code | nan |

### Observations
1. **Barcodes have leading zeros.** `gtin_upc` is 14 digits here
   (`00027000612323`), so it must stay as text. Some products may use a
   12-digit UPC in other rows or releases, so the same product could appear
   under two barcode lengths.
2. **Brand name can be blank while brand owner is filled.** A product's brand
   may need a fallback, using `brand_owner` when `brand_name` is missing.
3. **Some ingredient lists are vague.** "Vegetable Oil" doesn't say which oil,
   so it could contain palm oil without naming it. This can't be detected from
   the text.
4. **Dates are already in YYYY-MM-DD format**, so they convert cleanly to dates.
5. **Old records carry forward into new releases.** This row was last modified
   in 2020 but appears in the 2026 release, so each release is a full snapshot,
   not just new changes.
6. **Many columns are mostly blank** in this row, especially the newer ones
   (`trade_channel`, `short_description`, `material_code`). Older releases may
   not have them at all.
7. **There are 450 categories in total**, with 10630 rows in "No Listed Category."

### Decisions
- Keep `gtin_upc` as text in every layer.
- Treat ingredient text that names only "vegetable oil" without a specific oil
  as **not detectable**. Count it separately rather than as no palm ingrediant.

### Open questions
- Are barcodes stored with a consistent length, or do 12- and 14-digit versions
  of the same product both appear?
- How many rows have a blank `brand_name`?
- Should the filter script also keep `data_source` (for example, GDSN), to see
  whether the data source affects label quality?
- Which of the 450 categories belong to the chosen palm project groups?
