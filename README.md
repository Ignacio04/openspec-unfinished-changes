# Unfinished specification changes in OpenSpec

Replication package for an empirical study of the lifecycle of specification changes in Spec-Driven Development (SDD), using the [SpecMine](https://doi.org/10.5281/zenodo.22102779) dataset.

**Research question.** How often do OpenSpec specification changes remain unfinished, and what distinguishes them from completed ones?

Developed for CMP259 (Knowledge Discovery in Databases, PPGC/UFRGS) and intended for the MSR 2027 Mining Challenge.

## Contents

| Path | What it is |
|---|---|
| `scripts/download_data.py` | Downloads the full-census SpecMine tables used by the notebooks into `data_cache/` (selected columns and rows, about 140 MB). |
| `src/openspec_changes.py` | Builds the change table (one row per OpenSpec change), the lifecycle states, and the pending-task categories. Shared by the notebooks. |
| `notebooks/01_data_understanding.ipynb` | Business and data understanding: objectives, data sources, sanity checks, a prototype change table on the sample, task status, a first pass at lifecycle states, and sample vs. full-census comparison. |
| `notebooks/02_change_table.ipynb` | Change table for the full census (91,736 changes), validated against the sample; refined lifecycle states and how often changes remain unfinished (OM1); candidate mining features. |
| `outputs/<notebook>/` | Figures (PNG and PDF), tables (CSV), and `key_numbers.json` produced by each notebook. `outputs/02_change_table/change_table.parquet` is the mining table (derived, no text content). |
| `docs/kdd_cycle1.md` | First KDD cycle: the initial framing, what it found, and why the research question changed. |
| `requirements.txt` | Pinned Python dependencies. |

Notebooks are executed with their outputs included. Notebooks and docs are written in Portuguese.

## Data

This repository does **not** redistribute SpecMine data. Each mined repository keeps its own license.

1. **SpecMine 500-repository sample.** Clone it next to this repository, at the commit used in this study:

   ```bash
   git clone https://github.com/shyamagarwal13/specmine-official.git
   git -C specmine-official checkout da606c822ea8428d09d7e4321856c34672a4723a
   ```

   Expected layout:

   ```
   <parent>/
   ├── specmine-official/          # the sample (data/*.parquet, DATA_DICTIONARY.md)
   └── openspec-unfinished-changes/  # this repository
   ```

   To use another location, set the `SPECMINE_SAMPLE` environment variable to the clone's path.

2. **Full broad census.** `scripts/download_data.py` reads the needed columns and rows of five tables from the public [Hugging Face mirror](https://huggingface.co/datasets/ShyAgarwal/specmine) with DuckDB and caches them in `data_cache/`, which is not versioned. It needs internet access once; existing files are skipped.

## Reproducing

Tested with Python 3.14.3 on Windows 11.

```bash
pip install -r requirements.txt
python scripts/download_data.py
python -m nbconvert --to notebook --execute --inplace notebooks/01_data_understanding.ipynb
python -m nbconvert --to notebook --execute --inplace notebooks/02_change_table.ipynb
```

Notebook 02 checks its numbers against notebook 01, so run them in order. The analysis is deterministic (fixed bootstrap seed `20260711`); re-running it reproduces the numbers in each `outputs/<notebook>/key_numbers.json`.

## Citation of the dataset

```bibtex
@dataset{specmine_v1_2026,
  author    = {Agarwal, Shyam and Vasilescu, Bogdan},
  title     = {SpecMine: A Large-Scale Corpus of Spec-Driven Development Artifacts},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22102779}
}
```
