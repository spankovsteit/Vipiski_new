"""
PDF ingestion from inbox folder with **safe** deletion.

Problem solved
--------------
The legacy script deleted **all** files under the inbox after copying only those
whose filesystem ctime matched "today", which could destroy statements that
failed the date filter. Here we:

1. Copy **every** ``*.pdf`` found under the inbox (recursive ``rglob``).
2. Return the **source** paths that copied successfully.
3. Delete **only** those sources (plus try to remove now-empty subdirs).

If a copy fails, the source file remains for a retry on the next run.

Same-day re-runs **overwrite** an existing file with the same name in the day
folder (no ``stem_1.pdf`` suffixes).
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)


def ingest_pdfs(base_path: Path, src_dir_name: str, dest_dir: Path) -> list[Path]:
    """
    Copy PDFs from ``base_path / src_dir_name`` into ``dest_dir``.

    Parameters
    ----------
    base_path
        Root from settings (e.g. ``D:\\Выписки``).
    src_dir_name
        Inbox folder name (default ``Текущие``).
    dest_dir
        Day archive folder (``.../YYYY-MM/ddmmyyyy``).

    Returns
    -------
    list[Path]
        **Source** files that were copied successfully — used by
        ``remove_sources_only`` for deletion whitelist.
    """
    src_root = base_path / src_dir_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    if not src_root.is_dir():
        log.warning("Inbox folder does not exist: %s", src_root)
        return copied

    for path in sorted(src_root.rglob("*.pdf")):
        if not path.is_file():
            continue
        target = dest_dir / path.name
        try:
            if target.exists():
                log.info("Overwriting existing archive file %s", target.name)
            shutil.copy2(path, target)
            copied.append(path)
            log.info("Copied %s -> %s", path, target)
        except OSError as e:
            log.error("Failed to copy %s: %s", path, e)
    return copied


def remove_sources_only(processed_sources: list[Path]) -> None:
    """
    Remove inbox files that were successfully copied.

    Empty-directory cleanup is best-effort: Windows may keep a folder non-empty
    if something else created a file there concurrently.
    """
    for path in processed_sources:
        try:
            path.unlink(missing_ok=True)
            log.debug("Removed source %s", path)
        except OSError as e:
            log.warning("Could not remove %s: %s", path, e)

    if not processed_sources:
        return
    roots = {p.parent for p in processed_sources}
    for root in roots:
        try:
            # Deepest paths first so nested dirs empty before parents.
            for d in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                if d.is_dir():
                    try:
                        d.rmdir()
                    except OSError:
                        pass
        except OSError:
            pass
