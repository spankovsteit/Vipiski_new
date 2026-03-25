"""Filesystem tests for ``vipiski.files``."""

from __future__ import annotations

from pathlib import Path

from vipiski.files import ingest_pdfs, remove_sources_only


def test_ingest_pdfs_copies_and_overwrites(tmp_path: Path):
    base = tmp_path / "base"
    inbox = base / "inbox"
    inbox.mkdir(parents=True)
    dest = base / "2026-03" / "23032026"
    dest.mkdir(parents=True)

    pdf1 = inbox / "stmt.pdf"
    pdf1.write_bytes(b"%PDF-1.4 minimal")
    copied = ingest_pdfs(base, "inbox", dest)
    assert len(copied) == 1
    assert (dest / "stmt.pdf").exists()
    assert (dest / "stmt.pdf").read_bytes().startswith(b"%PDF")

    pdf1.write_bytes(b"%PDF second run")
    copied2 = ingest_pdfs(base, "inbox", dest)
    assert len(copied2) == 1
    assert b"second" in (dest / "stmt.pdf").read_bytes()


def test_ingest_pdfs_missing_inbox_returns_empty(tmp_path: Path):
    base = tmp_path / "empty_base"
    base.mkdir()
    out = ingest_pdfs(base, "нет_такой_папки", base / "dest")
    assert out == []


def test_remove_sources_only_deletes_files(tmp_path: Path):
    f = tmp_path / "x.pdf"
    f.write_text("x")
    remove_sources_only([f])
    assert not f.exists()
