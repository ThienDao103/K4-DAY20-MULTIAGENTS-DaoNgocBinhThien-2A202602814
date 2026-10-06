---
name: robust-data-cleaning-and-output-formatting
description: Use when processing CSV datasets, cleaning categorical/numeric fields, and writing structured JSON/CSV reports.
---
# Robust Data Cleaning and Output Formatting

1. Inspect input data thoroughly for duplicates, invalid values (e.g., missing markers), and inconsistent casing/formatting across categorical columns.
2. Deduplicate records strictly based on unique identifiers or exact rows as specified by the task rules.
3. Convert monetary values into integer cents before writing outputs to JSON or CSV files (e.g., multiply decimal amounts by 100 and round).
4. Populate all required metadata blocks and headers in output files (e.g., source file name, row counts, and canonical UTC timestamps).
