# 7. Per-user read/unread tracking: localStorage + optional private-Gist sync

Status: Accepted (2026-06-07)

## Context
Readers want to filter the catalog to **their own unread** summaries. The requirements:
per-user, cross-device, frequent (low-friction) marking — on a static, public, free
GitHub Pages site (no backend, ADR-0003) that has **no notion of the current user**.

## Decision
- **localStorage is the instant local cache** of `{canonical_key: marker}`, where
  `marker = <latest_version>__<summary_date>`. A paper is "read" only while the stored
  marker matches the current one, so a new version / updated summary re-surfaces it as
  unread. This works on Pages and dev with zero friction and **persists across deploys**.
- **Optional cross-device sync via a private GitHub Gist on the reader's own account.**
  Marking debounce-pushes the full map to the gist; opening pulls it (last-writer-wins).
  Auth is a fine-grained PAT (Gists: read/write) the reader pastes once per device, stored
  only in their browser and sent only to `api.github.com`. Without a token it's pure
  localStorage. A manual Export/Import (JSON) is also provided as a no-token backup.
- **Marking is manual** (explicit toggle on catalog cards and paper pages), not on-open.

## Alternatives rejected
- **Committed metadata** (read state in the repo, marked on dev, merged via PR): per-user
  "my unread" still needs an identity the static site doesn't have; every mark would be a
  commit/PR (untenable for frequent marking); mixes transient user state into authoritative
  metadata.
- **Hosted backend** (Supabase / Cloudflare Worker+KV / Firebase): true auto-sync but adds
  a service to run, secrets, and possible cost — departs from the pure-static, free model.

## Consequences
- (+) Meets per-user + cross-device + frequent on a free static site, no server we run.
- (−) Cross-device requires each reader to create + paste a GitHub token per device.
- (−) Last-writer-wins can drop a mark if two devices edit while offline simultaneously
  (rare for one person; could add per-entry timestamps later).
