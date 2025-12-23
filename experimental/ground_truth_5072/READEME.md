# Mapping 50.72 Sections Using `IRsWith5072.pkl`

This document explains the process used in `ens.ipynb` to map NRC 50.72 sections from the dataset provided in `IRsWith5072.pkl`.

## Overview

The notebook loads a dataset of incident reports and extracts references to 10 CFR 50.72 sections and ENS
(Event Notification System) using specifically the event numbers. The workflow includes data inspection,
filtering, extraction, and visualization.

## Steps Performed in `ens.ipynb`

1. **Load and Inspect Data**
   - The notebook loads the pickled DataFrame from `IRsWith5072.pkl`.
   - It displays the first few records to understand the structure and content.

2. **Filter for ENS/Retraction Records**
   - A function filters records whose `CONTENT` column contains keywords like 'retraction', 'EN', or 'ENS'.

3. **Extract 50.72 Sections and ENS Numbers**
   - Regular expressions are used to identify and extract references to 50.72 sections and ENS numbers from
     relevant text columns (`IMME_ACTN`, `CONTENT`, `REPO_BASI`).
   - The extraction logic is robust to various formats and ensures only valid section references are captured.
   - The results are combined into new columns: `50.72 section` and `ENS`.

4. **Result Summarization**
   - The notebook summarizes how many records contain 50.72 sections, ENS numbers, or both.
   - A filtered result is saved as `result_5072_only.csv` for further analysis.

5. **Visualization**
   - Bar plots are generated to show the frequency of each 50.72 section category, both overall and split by the
     `LER_LABEL` (indicating whether a Licensee Event Report is present).

## Key Functions

- **`extract_5072_sections`**: Extracts 50.72 section references from text using regex.
- **`extract_ens_number`**: Extracts ENS numbers from text.
- **`combine_5072_sections` / `combine_ens_sections`**: Aggregates extracted values from multiple columns.

## Output

- The processed data includes columns for AR number, mapped 50.72 sections, ENS numbers, and LER label.
- Visualizations help understand the distribution of section references in the dataset.

---

This workflow enables efficient mapping and analysis of NRC 50.72 section references in incident report data.
