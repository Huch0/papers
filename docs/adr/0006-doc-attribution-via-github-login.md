# 6. Doc attribution via GitHub login (not raw email)

Status: Accepted (2026-06-07)

## Context
Summaries, Concepts, and Q&A are written by an agent on behalf of a human (whoever
invoked `/summarize-paper` or `/paper-tutor`). Several lab-mates clone the repo, so we want
to attribute each doc to the person who curated it, shown on the (public) Website with
their name and avatar. The only ambient identity at authoring time is the git
`user.name`/`user.email`, which is not a GitHub login, and the site is public so raw
personal emails must not be committed.

## Decision
- **Field naming:** `curated_by` (the curator) + `contributors` (later editors) on Summaries
  and Concepts; `asked_by` per `<QA>` item. Named to avoid collision with a paper's
  `authors` (the researchers).
- **Identity resolution:** `config/contributors.yaml` maps git email → `{ github, name }`.
  At authoring time the harness reads `git config user.email`, resolves it, and stamps the
  **GitHub login** (not the email) into the doc. Unmapped → stamp the git name + flag to add
  a mapping; avatar falls back to a deterministic initials badge.
- **Avatars:** the public GitHub avatar URL `https://github.com/<login>.png` (no API key,
  no auth); initials-badge fallback when no login is known. (Rejected: Gravatar — needs the
  email + many users lack one; initials-only — no real photos.)
- **Privacy:** committed docs carry only `github login` + `display name`; raw emails live
  only in local `config/contributors.yaml`.

## Consequences
- (+) Real per-person attribution with avatars, zero API keys/secrets, public-safe.
- (+) Multi-contributor history (concepts get extended; Q&A is per-question).
- (−) Requires maintaining `config/contributors.yaml`; an unmapped contributor shows a
  name + initials badge until added.
- (−) Attribution is only as accurate as each clone's git identity (e.g. this repo's bg
  identity is `papers-harness` → mapped to a real login in contributors.yaml).
