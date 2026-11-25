"""Construction of the OpenSpec change table and lifecycle states.

One row per change: an ``openspec/changes/<name>/`` folder (active) or an
``openspec/changes/archive/YYYY-MM-DD-<name>/`` folder (archived). Shared by
the notebooks so the sample prototype and the full census use the same rules.
"""
import re

import numpy as np
import pandas as pd

RX_CHANGE = r'^(.*?openspec/changes/(?:archive/)?[^/]+)/'
RX_ARCHIVE_DATE = r'/changes/archive/(\d{4}-\d{2}-\d{2})'
UNCHECKED = re.compile(r'^\s*(?:[-*+]|\d+\.)\s*\[ \]\s*(.+)$', re.M)

# Heuristic, multi-label keyword categories for unchecked task items (exploratory).
PENDING_CATEGORIES = {
    'manual verification / QA': r'\b(?:manual(?:ly)?|verify|verification|validate|validation|smoke|qa|e2e|end[- ]to[- ]end|staging|sanity)\b',
    'automated tests': r'\b(?:tests?|testing|unit|integration|coverage|pytest|jest|vitest)\b',
    'documentation': r'\b(?:docs?|documentation|readme|changelog|comment)\b',
    'deploy / release / ops': r'\b(?:deploy\w*|release|rollout|publish|monitor\w*|production|prod|migrat\w*)\b',
    'optional / follow-up': r'\b(?:optional|follow[- ]?up|future|later|nice[- ]to[- ]have|defer\w*|tbd|stretch|out of scope)\b',
    'OpenSpec housekeeping': r'(?:openspec|\barchive\b)',
}
UNCATEGORIZED = 'uncategorized (likely implementation)'

# Refined lifecycle states (see notebooks/02_change_table.ipynb).
STATES = ['completed', 'completed with pending tasks', 'archived without task counts',
          'in progress', 'done, not archived', 'overtaken', 'stalled', 'stopped without task counts', 'undated']
POTENTIALLY_UNFINISHED = ['completed with pending tasks', 'overtaken', 'stalled']
UNCLOSED = ['done, not archived']


def change_dir(paths: pd.Series) -> pd.Series:
    """Change folder of each path, or NaN when the path is not inside openspec/changes/."""
    return paths.str.extract(RX_CHANGE)[0]


def build_change_table(artifacts: pd.DataFrame, code_refs: pd.DataFrame, deltas: pd.DataFrame,
                       obs_end: pd.Timestamp) -> pd.DataFrame:
    """Build the change table.

    artifacts: openspec_artifact_files rows (repo_name, file_path, kind, n_bytes, n_tasks, n_tasks_done).
    code_refs: openspec_code_refs rows (repo_name, artifact_path, code_path, exists_at_anchor).
    deltas:    one row per deduplicated spec delta file (repo_name, file_path, first, last), where
               first/last are commit timestamps (NaT allowed, e.g. for archived deltas).
    """
    a = artifacts.assign(change_dir=change_dir(artifacts.file_path)).dropna(subset=['change_dir'])
    a = a.assign(archived=a.change_dir.str.contains('/changes/archive/'))
    keys = ['repo_name', 'change_dir']
    tasks = a[a.kind.eq('tasks.md')]
    ch = a.groupby(keys).agg(
        archived=('archived', 'first'), n_artifacts=('kind', 'size'),
        has_proposal=('kind', lambda x: x.eq('proposal.md').any()),
        has_design=('kind', lambda x: x.eq('design.md').any()),
        has_tasks=('kind', lambda x: x.eq('tasks.md').any())).reset_index()
    ch = ch.merge(tasks.groupby(keys).agg(n_tasks=('n_tasks', 'sum'), n_done=('n_tasks_done', 'sum')),
                  on=keys, how='left')
    ch = ch.merge(a[a.kind.eq('proposal.md')].groupby(keys).n_bytes.sum().rename('proposal_bytes'),
                  on=keys, how='left')
    ch['n_pending'] = (ch.n_tasks - ch.n_done).where(ch.n_tasks > 0)
    ch['completion'] = (ch.n_done / ch.n_tasks).where(ch.n_tasks > 0)
    ch['archive_date'] = pd.to_datetime(ch.change_dir.str.extract(RX_ARCHIVE_DATE)[0], errors='coerce', utc=True)

    d = deltas.assign(change_dir=change_dir(deltas.file_path)).dropna(subset=['change_dir'])
    dg = d.groupby(keys).agg(n_spec_deltas=('file_path', 'size'), delta_first=('first', 'min'),
                             delta_last=('last', 'max'))
    ch = ch.merge(dg, on=keys, how='left')
    ch['n_spec_deltas'] = ch.n_spec_deltas.fillna(0).astype(int)

    cr = code_refs.assign(change_dir=change_dir(code_refs.artifact_path)).dropna(subset=['change_dir'])
    cg = cr.groupby(keys).agg(n_code_refs=('code_path', 'size'),
                              code_refs_exist_pct=('exists_at_anchor', lambda x: 100 * x.mean()))
    ch = ch.merge(cg, on=keys, how='left')
    ch['n_code_refs'] = ch.n_code_refs.fillna(0).astype(int)

    ch['repo_n_changes'] = ch.groupby('repo_name').change_dir.transform('size')
    ch['repo_last_archive'] = ch.groupby('repo_name').archive_date.transform('max')
    ch['idle_days'] = ((obs_end - ch.delta_last).dt.total_seconds() / 86400).where(~ch.archived)
    ch['later_archive'] = (ch.repo_last_archive > ch.delta_last.dt.floor('D')) & ~ch.archived
    return ch


def pending_items(tasks: pd.DataFrame) -> pd.DataFrame:
    """One row per unchecked task item, with heuristic category flags.

    tasks: tasks.md rows with repo_name, file_path and content.
    """
    t = tasks[tasks.content.notna()].assign(change_dir=lambda x: change_dir(x.file_path)).dropna(subset=['change_dir'])
    rows = [(r.repo_name, r.change_dir, '/changes/archive/' in r.change_dir, m.group(1).lower())
            for r in t.itertuples() for m in UNCHECKED.finditer(r.content)]
    it = pd.DataFrame(rows, columns=['repo_name', 'change_dir', 'archived', 'text'])
    for name, rx in PENDING_CATEGORIES.items():
        it[name] = it.text.str.contains(rx, regex=True)
    it[UNCATEGORIZED] = ~it[list(PENDING_CATEGORIES)].any(axis=1)
    return it


def assign_states(ch: pd.DataFrame, threshold_days: float) -> np.ndarray:
    """Refined lifecycle state of each change for an inactivity threshold (days)."""
    stopped = ch.idle_days >= threshold_days
    active = ~ch.archived
    return np.select(
        [ch.archived & ch.n_pending.eq(0),
         ch.archived & ch.n_pending.gt(0),
         ch.archived,
         active & ch.idle_days.isna(),
         active & ~stopped,
         active & stopped & ch.n_pending.eq(0),
         active & stopped & ch.n_pending.gt(0) & ch.later_archive,
         active & stopped & ch.n_pending.gt(0)],
        ['completed', 'completed with pending tasks', 'archived without task counts', 'undated',
         'in progress', 'done, not archived', 'overtaken', 'stalled'],
        'stopped without task counts')
