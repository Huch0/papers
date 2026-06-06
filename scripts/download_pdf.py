#!/usr/bin/env python3
"""download_pdf.py — fetch a PDF to a version directory with retries/backoff.

Refuses to overwrite an existing paper.pdf unless --force (the harness convention is
to create a NEW version directory rather than overwrite). Computes sha256 + bytes and
writes them back into the version metadata when run against a version dir.

Usage:
    download_pdf.py <url> --dir library/<slug>/v1
    download_pdf.py <url> --out path/to/paper.pdf
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import paperlib as pl

try:
    import requests
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False
    import urllib.request


def _ua() -> str:
    return pl.sources().get("defaults", {}).get(
        "user_agent", "papers-harness/1.0 (mailto:heochiyeong@gmail.com)")


def download(url: str, dest: Path, *, force: bool = False) -> dict:
    if dest.exists() and not force:
        raise FileExistsError(
            f"{dest} exists; create a new version dir instead of overwriting (use --force to override)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    retry = pl.sources().get("defaults", {}).get("retry", {})
    attempts = retry.get("max_attempts", 4)
    base = retry.get("backoff_base_seconds", 2.0)
    timeout = pl.sources().get("defaults", {}).get("request_timeout_seconds", 30)
    headers = {"User-Agent": _ua()}

    last_err = None
    for attempt in range(attempts):
        try:
            tmp = dest.with_suffix(".part")
            if HAVE_REQUESTS:
                r = requests.get(url, headers=headers, timeout=timeout, stream=True)
                r.raise_for_status()
                ctype = r.headers.get("Content-Type", "")
                with tmp.open("wb") as fh:
                    for chunk in r.iter_content(1 << 16):
                        fh.write(chunk)
            else:  # pragma: no cover
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    ctype = resp.headers.get("Content-Type", "")
                    tmp.write_bytes(resp.read())
            data = tmp.read_bytes()
            if not data.startswith(b"%PDF") and "pdf" not in ctype.lower():
                tmp.unlink(missing_ok=True)
                raise ValueError(f"response does not look like a PDF (Content-Type={ctype})")
            tmp.replace(dest)
            sha = pl.sha256_file(dest)
            size = pl.file_bytes(dest)
            pl.log_fetch("download_pdf", url=url, dest=pl.rel(dest), bytes=size, ok=True)
            return {"pdf_sha256": sha, "pdf_bytes": size, "path": pl.rel(dest)}
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < attempts - 1:
                time.sleep(base * (2 ** attempt))
    pl.log_error("download_pdf", str(last_err), url=url)
    pl.log_fetch("download_pdf", url=url, ok=False, error=str(last_err))
    raise RuntimeError(f"download failed after {attempts} attempts: {last_err}")


def _main() -> int:
    ap = argparse.ArgumentParser(description="Download a PDF with retries.")
    ap.add_argument("url")
    ap.add_argument("--dir", help="version dir; writes <dir>/paper.pdf and updates metadata")
    ap.add_argument("--out", help="explicit output path")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.dir:
        vdir = pl.resolve_path(args.dir)
        dest = vdir / "paper.pdf"
    elif args.out:
        dest = Path(args.out)
        vdir = None
    else:
        ap.error("provide --dir or --out")

    try:
        res = download(args.url, dest, force=args.force)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}")
        return 1

    print(f"downloaded {res['pdf_bytes']} bytes -> {res['path']} (sha {res['pdf_sha256'][:12]})")

    if args.dir:
        mf = vdir / "metadata.yaml"
        if mf.exists():
            meta = pl.load_yaml(mf)
            meta["pdf_sha256"] = res["pdf_sha256"]
            meta.setdefault("artifacts", {})["pdf"] = res["path"]
            meta.setdefault("status", {})["downloaded"] = True
            pl.dump_yaml(mf, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
