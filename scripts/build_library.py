"""Build a local SQLite/FTS5 index for the modelling reference library."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    year INTEGER,
    problem TEXT,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    text_status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_no INTEGER NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    content TEXT NOT NULL,
    UNIQUE(document_id, chunk_no)
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content, content='chunks', content_rowid='id', tokenize='trigram'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE OF content ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE INDEX IF NOT EXISTS idx_documents_year_problem ON documents(year, problem);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id, chunk_no);
"""


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(path: Path, root: Path) -> tuple[str, int | None, str | None]:
    relative = path.relative_to(root).as_posix()
    year_match = re.search(r"20\d{2}", relative)
    year = int(year_match.group()) if year_match else None
    problem = None
    for part in reversed(path.parts):
        match = re.match(r"([A-F])(?:题|题优秀论文|$)", part, re.IGNORECASE)
        if match:
            problem = match.group(1).upper()
            break
    if problem is None:
        match = re.match(r"([A-F])\d", path.stem, re.IGNORECASE)
        if match:
            problem = match.group(1).upper()
    kind = "paper_pdf" if path.suffix.lower() == ".pdf" else "project_markdown"
    return kind, year, problem


def split_text(text: str, page_size: int = 6000, overlap: int = 500):
    pages = [page.strip() for page in text.split("\f") if page.strip()]
    if not pages and text.strip():
        pages = [text.strip()]
    for page_no, page in enumerate(pages, start=1):
        start = 0
        while start < len(page):
            end = min(start + page_size, len(page))
            content = page[start:end].strip()
            if content:
                yield page_no, page_no, content
            if end == len(page):
                break
            start = max(end - overlap, start + 1)


def extract_text(path: Path) -> tuple[str, str]:
    if path.suffix.lower() == ".md":
        return path.read_text(encoding="utf-8"), "ok"
    executable = shutil.which("pdftotext")
    if not executable:
        return "", "missing_pdftotext"
    result = subprocess.run(
        [executable, "-layout", "-enc", "UTF-8", str(path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    status = "ok" if result.stdout.strip() else f"empty_exit_{result.returncode}"
    return result.stdout, status


def iter_sources(root: Path):
    for directory in (root / "references", root / "research", root / "prompts"):
        if directory.exists():
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.suffix.lower() in {".pdf", ".md"}:
                    yield path


def build(root: Path, db_path: Path, force: bool = False) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if force and db_path.exists():
        db_path.unlink()
    connection = sqlite3.connect(db_path)
    connection.executescript(SCHEMA)
    now = datetime.now(timezone.utc).isoformat()
    seen: set[str] = set()
    counts: dict[str, int] = {}
    for path in iter_sources(root):
        relative = path.relative_to(root).as_posix()
        seen.add(relative)
        kind, year, problem = classify(path, root)
        content, text_status = extract_text(path)
        stat = path.stat()
        connection.execute("DELETE FROM documents WHERE path = ?", (relative,))
        cursor = connection.execute(
            """INSERT INTO documents
            (path, title, source_kind, year, problem, size_bytes, sha256,
             modified_at, indexed_at, text_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (relative, path.stem, kind, year, problem, stat.st_size,
             file_hash(path), datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
             now, text_status),
        )
        document_id = cursor.lastrowid
        for chunk_no, (page_start, page_end, chunk) in enumerate(split_text(content), start=1):
            connection.execute(
                """INSERT INTO chunks
                (document_id, chunk_no, page_start, page_end, content)
                VALUES (?, ?, ?, ?, ?)""",
                (document_id, chunk_no, page_start, page_end, chunk),
            )
        counts[kind] = counts.get(kind, 0) + 1
    placeholders = ",".join("?" for _ in seen) or "''"
    stale = connection.execute(
        f"SELECT id FROM documents WHERE path NOT IN ({placeholders})", tuple(seen)
    ).fetchall()
    for (document_id,) in stale:
        connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('optimize')")
    connection.commit()
    total_docs = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    total_chunks = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    connection.close()
    print(f"indexed documents: {total_docs}")
    print(f"indexed chunks: {total_chunks}")
    print(f"source kinds: {counts}")
    print(f"database: {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--force", action="store_true", help="rebuild from scratch")
    args = parser.parse_args()
    root = args.root.resolve()
    build(root, (args.db or root / "research" / "library.db").resolve(), args.force)


if __name__ == "__main__":
    main()
