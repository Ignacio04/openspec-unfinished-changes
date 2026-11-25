#!/usr/bin/env python3
"""Download the SpecMine full-census tables used by the notebooks into data_cache/.

Reads only the needed columns and rows from the public Hugging Face mirror of
SpecMine v1.0 (https://huggingface.co/datasets/ShyAgarwal/specmine) with DuckDB
over HTTP range requests. Files that already exist are skipped.

    python scripts/download_data.py
"""
from pathlib import Path
import time

import duckdb

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'data_cache'
HF = 'https://huggingface.co/datasets/ShyAgarwal/specmine/resolve/main/data/'
OSA = f"read_parquet('{HF}openspec_artifact_files.parquet')"

QUERIES = {
    # 13 columns of every broad-census spec file
    'full_spec_files_slim':
        'SELECT file_url_sha16, repo_name, file_path, spec_tool, spec_role, file_total_commits, commit_history_status, '
        'file_first_commit_at, file_last_commit_at, repo_pushed_at, repo_stars, repo_archived, repo_fork '
        f"FROM read_parquet('{HF}spec_files.parquet')",
    # every OpenSpec artifact, without its text
    'full_openspec_artifacts_meta':
        f'SELECT repo_name, file_path, kind, n_bytes, n_tasks, n_tasks_done, n_code_refs, fetch_status, fetched_at FROM {OSA}',
    # text of tasks.md files, to classify unchecked items
    'full_openspec_tasks_content':
        f"SELECT repo_name, file_path, content FROM {OSA} WHERE kind = 'tasks.md'",
    # task-to-code references
    'full_openspec_code_refs':
        'SELECT repo_name, artifact_path, code_path, task_done, exists_at_anchor '
        f"FROM read_parquet('{HF}openspec_code_refs.parquet')",
    # commits of spec deltas of active changes (dates of the last activity of each change)
    'full_active_delta_commits':
        'SELECT file_url_sha16, repo_name, file_path, commit_sha, committed_at '
        f"FROM read_parquet('{HF}spec_file_commits.parquet') "
        "WHERE file_path LIKE '%openspec/changes/%' AND file_path NOT LIKE '%/changes/archive/%'",
}


def main():
    CACHE.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute('SET enable_progress_bar=false; INSTALL httpfs; LOAD httpfs;')
    for name, sql in QUERIES.items():
        path = CACHE / f'{name}.parquet'
        if path.exists():
            print(f'{name}: cached ({path.stat().st_size / 1e6:.1f} MB)')
            continue
        t0 = time.time()
        con.execute(f"COPY ({sql}) TO '{path.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
        print(f'{name}: downloaded in {time.time() - t0:.0f} s ({path.stat().st_size / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()
