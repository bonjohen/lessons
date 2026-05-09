---
title: Harvester Design Decisions
summary: Key choices in building the lesson harvester — recursive scanning, path-based slugs, and integrated export generation.
date: 2026-05-08
phase: implementation
lesson_type: architecture
status: active
tags: [python, harvesting, slug-generation, architecture]
---

## Context

The Lessons Hub harvester (`scripts/harvest_lessons.py`) needs to clone multiple GitHub repos, find markdown lesson files, parse frontmatter, normalize metadata, and generate both JSON indexes and AI-readable export packs.

## Key Decisions

### Recursive Markdown Scanning

Source repos may organize lessons in subdirectories (e.g., `docs/lessons/block1/*.md`). The harvester uses `pathlib.rglob("*.md")` instead of a flat glob, discovering lessons at any depth below the configured `lessons_path`.

### Path-Based Slug Generation

When lessons live in subdirectories, filename-only slugs cause collisions (multiple `index.md` files → duplicate IDs). The slug includes the relative path from the lessons root: `block1/index.md` → `block1-index`, making IDs unique without requiring explicit `slug` frontmatter.

### Integrated Export Generation

Rather than a separate `build_exports.py` script, export generation was integrated directly into the harvester. This avoids a second pass over the data and ensures exports are always in sync with generated JSON. The `build:full` pipeline runs harvest once and gets both outputs.

### Windows Compatibility

Git clone creates read-only files on Windows that `shutil.rmtree` can't delete by default. The harvester uses a custom `onexc` handler to chmod files before deletion, making the cleanup step cross-platform.

## Key Takeaway

Design for the messiest real-world input first. Subdirectory lessons and duplicate filenames appeared immediately when harvesting real repos — handling them from the start saved significant rework.
