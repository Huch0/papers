#!/usr/bin/env python3
"""paperlib — shared utilities for the papers/ research harness.

Single source of truth for: root detection, the on-disk schema, canonical-key
derivation, slugs, hashing, YAML I/O, and config loading. Every other script
imports from here so validation/indexing/scoring/fetching never drift apart.

Pure standard library + PyYAML. No network. Safe to import anywhere.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("PyYAML is required: pip install pyyaml\n")
    raise

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

# scripts/ lives directly under the papers/ root, so root is two levels up.
ROOT = Path(__file__).resolve().parent.parent

CONFIG = ROOT / "config"
REGISTRY = ROOT / "registry"
INDEXES = ROOT / "indexes"
LIBRARY = ROOT / "library"
INBOX = ROOT / "inbox"
LOGS = ROOT / "logs"
KNOWLEDGE = ROOT / "knowledge"
CONCEPTS = KNOWLEDGE / "concepts"
SESSIONS = KNOWLEDGE / "sessions"

PAPERS_JSONL = REGISTRY / "papers.jsonl"
FETCH_LOG = REGISTRY / "fetch_log.jsonl"
DUP_CANDIDATES = REGISTRY / "duplicate_candidates.jsonl"
ALIASES = REGISTRY / "aliases.yaml"
ERRORS_JSONL = LOGS / "errors.jsonl"
CATALOG_SQLITE = REGISTRY / "catalog.sqlite"

TRIAGE_LABELS = ["MUST_READ", "READ_SOON", "SKIM", "TRACK_ONLY", "SKIP"]
SUMMARY_STATUSES = ["none", "triage_only", "full", "stale"]
READ_STATUSES = ["unread", "reading", "read", "abandoned"]

# --------------------------------------------------------------------------- #
# Time
# --------------------------------------------------------------------------- #

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S%z", "%Y%m%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def days_since(s: str | None) -> float | None:
    dt = parse_date(s)
    if dt is None:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0

# --------------------------------------------------------------------------- #
# YAML / JSON I/O
# --------------------------------------------------------------------------- #

def load_yaml(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if data is not None else default


def dump_yaml(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=100)
    tmp.replace(p)


def read_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    out: list[dict] = []
    if not p.exists():
        return out
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(p)


def append_jsonl(path: str | Path, row: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def log_error(stage: str, message: str, **extra: Any) -> None:
    row = {"ts": now_iso(), "stage": stage, "message": message}
    row.update(extra)
    append_jsonl(ERRORS_JSONL, row)


def log_fetch(source: str, **fields: Any) -> None:
    row = {"ts": now_iso(), "source": source}
    row.update(fields)
    append_jsonl(FETCH_LOG, row)


# --------------------------------------------------------------------------- #
# Markdown front-matter (for the knowledge base notes)
# --------------------------------------------------------------------------- #

def load_md_frontmatter(path: str | Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) for a markdown file with a YAML --- block.
    Missing file -> ({}, ""). No front-matter -> ({}, whole_text)."""
    p = Path(path)
    if not p.exists():
        return {}, ""
    text = p.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            return (meta if isinstance(meta, dict) else {}), parts[2].lstrip("\n")
    return {}, text


def dump_md_frontmatter(path: str | Path, meta: dict, body: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=100).strip()
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(f"---\n{fm}\n---\n\n{body.lstrip()}\n", encoding="utf-8")
    tmp.replace(p)

# --------------------------------------------------------------------------- #
# Config loaders (cached)
# --------------------------------------------------------------------------- #

_CONFIG_CACHE: dict[str, Any] = {}

def _cfg(name: str) -> Any:
    if name not in _CONFIG_CACHE:
        _CONFIG_CACHE[name] = load_yaml(CONFIG / name, default={})
    return _CONFIG_CACHE[name]


def interests() -> dict:
    return _cfg("interests.yaml")


def sources() -> dict:
    return _cfg("sources.yaml")


def venues() -> dict:
    return _cfg("venues.yaml")


def scoring_cfg() -> dict:
    return _cfg("scoring.yaml")


def tag_taxonomy() -> dict:
    return _cfg("tag_taxonomy.yaml")


def milestones_cfg() -> dict:
    return _cfg("milestones.yaml")


PRIORITY_WEIGHT = {"very_high": 1.0, "high": 0.8, "medium": 0.55, "low": 0.3}

# --------------------------------------------------------------------------- #
# Text normalization, slugs, hashing
# --------------------------------------------------------------------------- #

_WS = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_title(title: str) -> str:
    t = (title or "").lower().strip()
    t = _NON_ALNUM.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    return t


def title_hash(title: str) -> str:
    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()


def slugify(text: str, max_words: int = 8) -> str:
    words = normalize_title(text).split()[:max_words]
    s = "-".join(words)
    return s or "untitled"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_bytes(path: str | Path) -> int:
    return Path(path).stat().st_size

# --------------------------------------------------------------------------- #
# arXiv / DOI id parsing
# --------------------------------------------------------------------------- #

_ARXIV_NEW = re.compile(r"(\d{4}\.\d{4,5})(v(\d+))?")
_ARXIV_OLD = re.compile(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v(\d+))?")
_DOI = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.IGNORECASE)
_OPENREVIEW = re.compile(r"[?&]id=([A-Za-z0-9_\-]+)")


def parse_arxiv_id(text: str) -> tuple[str | None, str | None]:
    """Return (base_id, version) e.g. ('2501.12345', 'v2'). Version may be None."""
    if not text:
        return None, None
    m = _ARXIV_NEW.search(text)
    if not m:
        m = _ARXIV_OLD.search(text)
    if not m:
        return None, None
    base = m.group(1)
    ver = m.group(2)  # includes the leading 'v'
    return base, ver


def parse_doi(text: str) -> str | None:
    if not text:
        return None
    m = _DOI.search(text)
    if not m:
        return None
    return m.group(0).rstrip(".,;)")


def parse_openreview_id(text: str) -> str | None:
    if not text:
        return None
    m = _OPENREVIEW.search(text)
    return m.group(1) if m else None


def classify_source(ref: str) -> str:
    """Classify an /add-paper argument into a source type."""
    r = ref.strip()
    low = r.lower()
    if os.path.exists(r) and r.lower().endswith(".pdf"):
        return "local_pdf"
    if "arxiv.org" in low or parse_arxiv_id(r)[0] and not low.startswith("http"):
        if "arxiv.org" in low or re.fullmatch(r"\s*(arxiv:)?\d{4}\.\d{4,5}(v\d+)?\s*", low):
            return "arxiv"
    if "openreview.net" in low:
        return "openreview"
    if "semanticscholar.org" in low:
        return "semantic_scholar"
    if "openalex.org" in low:
        return "openalex"
    if low.startswith("10.") or "doi.org" in low or parse_doi(r):
        return "doi"
    if low.endswith(".pdf") or "/pdf" in low:
        return "pdf_url"
    if low.startswith("http"):
        return "url"
    if parse_arxiv_id(r)[0]:
        return "arxiv"
    return "unknown"

# --------------------------------------------------------------------------- #
# Canonical key / slug derivation
# --------------------------------------------------------------------------- #

def derive_canonical_key(ids: dict, title: str = "") -> str:
    """Derive a stable canonical key from identifiers, falling back to title hash."""
    arx = ids.get("arxiv_base_id")
    if arx:
        return f"arxiv-{arx}"
    doi = ids.get("doi")
    if doi:
        return "doi-" + _NON_ALNUM.sub("-", doi.lower()).strip("-")
    orv = ids.get("openreview_id")
    if orv:
        return f"openreview-{orv}"
    s2 = ids.get("semantic_scholar_id")
    if s2:
        return f"s2-{s2}"
    oa = ids.get("openalex_id")
    if oa:
        return "openalex-" + oa.rsplit("/", 1)[-1]
    return "title-" + title_hash(title)[:12]


def derive_slug(canonical_key: str, title: str) -> str:
    """Human-readable, collision-resistant dir name."""
    suffix = canonical_key.split("-", 1)[-1].replace(".", "").replace("/", "")[-10:]
    base = slugify(title, max_words=7)
    return f"{base}-{suffix}" if suffix else base

# --------------------------------------------------------------------------- #
# Library traversal
# --------------------------------------------------------------------------- #

def iter_paper_dirs() -> Iterator[Path]:
    if not LIBRARY.exists():
        return
    for child in sorted(LIBRARY.iterdir()):
        if child.is_dir() and (child / "paper.yaml").exists():
            yield child


def load_paper(slug_or_dir: str | Path) -> dict | None:
    d = Path(slug_or_dir)
    if not d.is_absolute():
        d = LIBRARY / slug_or_dir
    pf = d / "paper.yaml"
    return load_yaml(pf) if pf.exists() else None


def iter_papers() -> Iterator[dict]:
    for d in iter_paper_dirs():
        rec = load_yaml(d / "paper.yaml")
        if rec:
            yield rec


def find_paper_by_key(canonical_key: str) -> Path | None:
    for d in iter_paper_dirs():
        rec = load_yaml(d / "paper.yaml")
        if rec and rec.get("canonical_key") == canonical_key:
            return d
    return None


def version_dir(paper_dir: Path, version_key: str) -> Path:
    return Path(paper_dir) / version_key


def next_version_key(paper: dict) -> str:
    existing = [v.get("version_key", "") for v in paper.get("versions", [])]
    nums = [int(v[1:]) for v in existing if re.fullmatch(r"v\d+", v)]
    return f"v{max(nums) + 1 if nums else 1}"


def rel(path: str | Path) -> str:
    """Path relative to ROOT, POSIX form, for storage in metadata."""
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def resolve_path(path: str | Path) -> Path:
    """Resolve a user/skill-supplied path robustly.

    Absolute paths are used as-is. Relative paths are tried against the current
    working directory first, then the papers ROOT; if neither exists yet (e.g. a
    path to be created), fall back to ROOT/path so writes land inside the harness.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    cwd_p = (Path.cwd() / p)
    if cwd_p.exists():
        return cwd_p
    root_p = (ROOT / p)
    if root_p.exists():
        return root_p
    return root_p

# --------------------------------------------------------------------------- #
# Record templates
# --------------------------------------------------------------------------- #

def new_paper_record(canonical_key: str, slug: str, title: str) -> dict:
    return {
        "canonical_key": canonical_key,
        "slug": slug,
        "title": title,
        "authors": [],
        "year": None,
        "primary_ids": {
            "doi": None, "arxiv_base_id": None, "openreview_id": None,
            "semantic_scholar_id": None, "openalex_id": None,
        },
        "canonical_urls": [],
        "topic_groups": [],
        "tags": [],
        "venue": {"name": None, "tier": None, "status": None, "year": None},
        "user": {"read_status": "unread", "triage_label": None,
                 "triage_confidence": None, "notes": None},
        "milestone": None,        # {field, era, significance} when curated as a landmark
        "knowledge_concepts": [], # concept slugs in knowledge/ linked to this paper
        "versions": [],
        "relations": {"duplicate_candidates": [], "related_papers": [],
                      "supersedes": [], "superseded_by": []},
    }


def new_version_metadata(canonical_key: str, version_key: str, title: str) -> dict:
    return {
        "canonical_key": canonical_key,
        "version_key": version_key,
        "title": title,
        "authors": [],
        "abstract": "Not reported",
        "venue": None,
        "year": None,
        "source": None,
        "source_url": None,
        "pdf_url": None,
        "pdf_sha256": None,
        "fetched_at": now_iso(),
        "source_updated_at": None,
        "ids": {"doi": None, "arxiv_id": None, "arxiv_base_id": None,
                "arxiv_version": None, "openreview_id": None,
                "semantic_scholar_id": None, "openalex_id": None},
        "tags": [],
        "topic_groups": [],
        "scoring": {"score": None, "label": None, "confidence": None,
                    "rationale": "", "matched_interests": [],
                    "negative_signals": [], "subscores": {}},
        "artifacts": {"pdf": None, "extraction": None, "summary": None,
                      "code_url": None, "project_url": None, "dataset_url": None},
        "status": {"downloaded": False, "extracted": False, "summarized": False,
                   "triaged": False, "user_read_status": "unread"},
    }


if __name__ == "__main__":
    # Tiny smoke test / introspection.
    print("ROOT:", ROOT)
    print("papers in library:", sum(1 for _ in iter_paper_dirs()))
    print("interests groups:", list(interests().get("topic_groups", {}).keys()))
