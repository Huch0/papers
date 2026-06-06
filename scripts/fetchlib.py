#!/usr/bin/env python3
"""fetchlib — shared HTTP + candidate normalization for fetch_*.py scripts.

Provides polite HTTP GET with retry/backoff and a normalized "candidate" builder so
every source emits the same record shape that ingest.py consumes.
"""
from __future__ import annotations

import time
from typing import Any

import paperlib as pl

try:
    import requests
    HAVE_REQUESTS = True
except ImportError:  # pragma: no cover
    HAVE_REQUESTS = False
    import urllib.request
    import urllib.error


def _defaults() -> dict:
    return pl.sources().get("defaults", {})


def user_agent() -> str:
    return _defaults().get("user_agent", "papers-harness/1.0")


def http_get(url: str, *, params: dict | None = None, headers: dict | None = None,
             source: str = "http", accept_json: bool = False) -> tuple[int, str]:
    """GET with retry/backoff. Returns (status_code, text). Raises on total failure."""
    d = _defaults()
    retry = d.get("retry", {})
    attempts = retry.get("max_attempts", 4)
    base = retry.get("backoff_base_seconds", 2.0)
    timeout = d.get("request_timeout_seconds", 30)
    hdrs = {"User-Agent": user_agent()}
    if accept_json:
        hdrs["Accept"] = "application/json"
    if headers:
        hdrs.update(headers)

    last_err: Any = None
    for attempt in range(attempts):
        try:
            if HAVE_REQUESTS:
                r = requests.get(url, params=params, headers=hdrs, timeout=timeout)
                if r.status_code == 429 or r.status_code >= 500:
                    raise RuntimeError(f"HTTP {r.status_code}")
                return r.status_code, r.text
            else:  # pragma: no cover
                import urllib.parse
                full = url + ("?" + urllib.parse.urlencode(params) if params else "")
                req = urllib.request.Request(full, headers=hdrs)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.status, resp.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < attempts - 1:
                time.sleep(base * (2 ** attempt))
    pl.log_error(f"fetch.{source}", f"GET failed: {last_err}", url=url)
    raise RuntimeError(f"GET {url} failed after {attempts} attempts: {last_err}")


def make_candidate(*, title: str, source: str, source_url: str | None = None,
                   authors: list[str] | None = None, abstract: str | None = None,
                   year: int | None = None, venue: Any = None,
                   pdf_url: str | None = None, source_updated_at: str | None = None,
                   ids: dict | None = None, code_url: str | None = None,
                   project_url: str | None = None, extra: dict | None = None) -> dict:
    """Build a normalized candidate record (the shape ingest.py expects)."""
    ids = ids or {}
    # normalize arxiv id parts if an arxiv_id was supplied
    if ids.get("arxiv_id") and not ids.get("arxiv_base_id"):
        base, ver = pl.parse_arxiv_id(ids["arxiv_id"])
        ids["arxiv_base_id"] = base
        ids.setdefault("arxiv_version", ver)
    cand = {
        "title": (title or "").strip(),
        "authors": authors or [],
        "abstract": abstract or "Not reported",
        "year": year,
        "venue": venue,
        "source": source,
        "source_url": source_url,
        "pdf_url": pdf_url,
        "source_updated_at": source_updated_at,
        "ids": {
            "doi": ids.get("doi"),
            "arxiv_id": ids.get("arxiv_id"),
            "arxiv_base_id": ids.get("arxiv_base_id"),
            "arxiv_version": ids.get("arxiv_version"),
            "openreview_id": ids.get("openreview_id"),
            "semantic_scholar_id": ids.get("semantic_scholar_id"),
            "openalex_id": ids.get("openalex_id"),
        },
        "tags": [],
        "topic_groups": match_topic_groups(title, abstract),
        "code_url": code_url,
        "project_url": project_url,
    }
    if extra:
        cand.update(extra)
    return cand


def match_topic_groups(title: str | None, abstract: str | None) -> list[str]:
    text = f"{title or ''} {abstract or ''}".lower()
    groups = pl.interests().get("topic_groups", {})
    out = []
    for name, g in groups.items():
        if any(k.lower() in text for k in g.get("keywords", [])):
            out.append(name)
    return out


def keyword_query_terms() -> list[str]:
    """Flatten interest keywords for query building (deduped, longest first)."""
    groups = pl.interests().get("topic_groups", {})
    terms: set[str] = set()
    for g in groups.values():
        for k in g.get("keywords", []):
            terms.add(k)
    return sorted(terms, key=len, reverse=True)
