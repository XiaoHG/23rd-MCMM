"""Search the local modelling reference library."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path


def fts_query(query: str) -> str:
    terms = [term for term in re.split(r"\s+", query.strip()) if term]
    return " AND ".join('"' + term.replace('"', " ") + '"' for term in terms)


def search(db_path: Path, query: str, year: int | None, problem: str | None,
           source_kind: str | None, limit: int):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    filters = []
    values: list[object] = []
    if year is not None:
        filters.append("d.year = ?")
        values.append(year)
    if problem:
        filters.append("d.problem = ?")
        values.append(problem.upper())
    if source_kind:
        filters.append("d.source_kind = ?")
        values.append(source_kind)
    where = (" AND " + " AND ".join(filters)) if filters else ""
    rows = []
    if query.strip():
        sql = f"""SELECT d.path, d.title, d.source_kind, d.year, d.problem,
            c.page_start, c.page_end,
            snippet(chunks_fts, 0, '[', ']', '...', 32) AS snippet,
            bm25(chunks_fts) AS score
            FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.rowid
            JOIN documents d ON d.id = c.document_id
            WHERE chunks_fts MATCH ?{where}
            ORDER BY score LIMIT ?"""
        try:
            rows = connection.execute(sql, [fts_query(query), *values, limit]).fetchall()
        except sqlite3.OperationalError:
            rows = []
    if not rows:
        terms = [term for term in re.split(r"\s+", query.strip()) if term]
        if not terms:
            terms = [""]
        like_conditions = " AND ".join("c.content LIKE ?" for _ in terms)
        sql = f"""SELECT d.path, d.title, d.source_kind, d.year, d.problem,
            c.page_start, c.page_end,
            substr(replace(c.content, char(10), ' '), 1, 360) AS snippet,
            0.0 AS score
            FROM chunks c JOIN documents d ON d.id = c.document_id
            WHERE {like_conditions}{where}
            ORDER BY d.year DESC, d.problem, d.path, c.chunk_no LIMIT ?"""
        rows = connection.execute(sql, [*(f"%{term}%" for term in terms), *values, limit]).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="", help="keywords or phrase")
    parser.add_argument("--db", type=Path, default=Path("research/library.db"))
    parser.add_argument("--year", type=int)
    parser.add_argument("--problem", choices=list("ABCDEF"))
    parser.add_argument("--kind", dest="source_kind", choices=["paper_pdf", "project_markdown"])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = search(args.db, args.query, args.year, args.problem, args.source_kind, args.limit)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if not results:
        print("No matching documents.")
        return
    for index, item in enumerate(results, start=1):
        page = f"p.{item['page_start']}" if item["page_start"] else ""
        print(f"{index}. [{item['year'] or '-'} {item['problem'] or '-'}] {item['title']} {page}")
        print(f"   {item['path']}")
        print(f"   {item['snippet']}")


if __name__ == "__main__":
    main()
