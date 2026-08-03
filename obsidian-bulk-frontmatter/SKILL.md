---
name: obsidian-bulk-frontmatter
description: "Bulk-normalize Obsidian tags; handles multi-line YAML."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [obsidian, frontmatter, tags, bulk-edit, vault-ops]
    category: custom
---

# Obsidian Bulk Frontmatter

Bulk-normalize a frontmatter field — most often `tags:` — across a whole folder of
notes, applying a single canonical schema (e.g. a tag namespace like
`心智模型/xxx` without `#` prefix or quotes).

This complements the bundled `obsidian` skill (single-note ops) with the
multi-file normalization workflow and its specific failure modes.

## When to use

- Applying a uniform `tags:` schema to dozens/hundreds of notes.
- Migrating tag formats (e.g. `#心智模型/X` → `心智模型/X`, quoted → unquoted).
- Stripping an obsolete namespace (e.g. dropping `常青卡片` / `mental-model` markers).
- Any "rewrite this field the same way in N files" job.

## The naive approach fails — read this first

A single-line regex `^tags: \[.*\]$` silently misses notes whose frontmatter
uses the **multi-line YAML sequence form**:

```yaml
tags:
  - "心智模型/心理学"
  - "心智模型/元认知与思维方法论"
```

Notes in this form are left untouched and you declare false success.

## Robust procedure

1. **Parse the full block, both shapes.** Match
   `tags:(\[.*?\]|\n(?:\s*-\s*.+\n)+)` and collect items from whichever branch matched.
2. **Normalize each item.** Strip leading `#`, strip surrounding `"`/`'`, strip
   whitespace. Emit `心智模型/心理学`, never `"#心智模型/心理学"`.
3. **Drop non-conforming items.** If a note carries a stray tag that isn't in your
   namespace (e.g. a leftover `dd`, a topic tag that no longer belongs), DISCARD it
   rather than preserving it. Log what was dropped.
4. **Rewrite as single-line list.** `tags: [心智模型/心理学, 心智模型/元认知与思维方法论]`.
5. **Self-verify in a second pass.** Assert every surviving `tags:` line matches
   `^tags: \[(NAMESPACE/[^,\s]+(, )?)+\]$` and print any offender. Do NOT trust the
   write pass — surface anomalies and re-run.

## Implementation guidance

Prefer a single Python script (in `execute_code`, or `scripts/normalize_tags.py`)
that reads each file, parses, rewrites, and self-verifies in one pass. This is far
safer than N separate `patch` calls and inherently catches the multi-line / dirty
cases. Keep the namespace a parameter so the same script serves future re-schemas.

## Pitfalls

- Multi-line YAML `tags:` blocks are common and easy to miss — always handle both forms.
- Dirty/orphan tags from a prior schema WILL slip through if you only preserve-and-strip;
  explicitly filter by namespace.
- Never declare success from the write pass alone; the verify pass is mandatory.
- Quote noise (`"#心智模型/X"`) and `#` prefix are interchangeable leftovers — strip both.
- Leave `category:` / `name` / `description` / `source` / `status` untouched — only edit
  the target field.

See `scripts/normalize_tags.py` for a reusable, namespace-parameterized implementation.
