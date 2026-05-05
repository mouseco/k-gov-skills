---
name: hwpx-autofill-conversion
description: Use when the user provides or asks about a Korean HWPX document, .hwpx template, Hangul form, public-sector report form, placeholder replacement, semantic slot mapping, or HWPX-based document generation. Supports inspecting HWPX ZIP/XML structure, drafting and reviewing slot maps, filling templates while preserving styles/tables/assets, repacking to .hwpx, and validating Korean UTF-8 text. Does not directly edit legacy binary .hwp files.
---

# HWPX Autofill Conversion

Use this skill for `.hwpx` template filling, Korean public-sector report forms, and document generation where the final output must remain an HWPX file.

## Core Rules

- Support `.hwpx` only. If the source is `.hwp`, ask for an HWPX export first.
- Treat every user template as potentially sensitive. Do not publish, copy, or commit user-provided templates unless confirmed public-safe.
- Preserve existing document structure and styles. Prefer replacing existing text nodes or cloning existing blocks over inventing new layout.
- Keep table geometry, section count, style IDs, `BinData`, and package manifest entries intact unless the user explicitly asks for layout changes.
- Read and write XML as UTF-8. Never reuse garbled console text, replacement characters, or mojibake.
- Do not rely on a single hard-coded public template. The skill must inspect the user's actual template.

## Workflow

1. **Inspect the template**
   - Confirm the extension is `.hwpx`.
   - Unzip/read the package as a ZIP.
   - Inspect `Contents/header.xml`, `Contents/content.hpf`, and `Contents/section*.xml`.
   - Identify paragraphs, tables, placeholders, repeated blocks, style references, and package assets.

2. **Choose the execution path**
   - Simple placeholder replacement: edit existing `<hp:t>` text nodes and repack.
   - New or unfamiliar public report template: run `inspect -> slot map draft -> human review -> compile -> QA`.
   - Known bundled public report template: read the matching profile in `profiles/` first, then use its `template_file` under `templates/`.
   - Known template with reviewed slot map: compile from the reviewed slot map.
   - If XML editing is not enough for page-render behavior, field interaction, or editor-level operations, consider the local `rhwp` runner only after explaining the tradeoff.

3. **Fill or generate content**
   - Use Korean public-sector report structure when writing: `background/current state -> issue/need -> direction -> tasks -> management/expected effect -> next action` when appropriate.
   - Use concise Korean administrative style (`~함`, `~필요`, `~예정`) without unnecessary final periods.
   - Use bold markers in JSON/content only for short key phrases; the tools can convert `**text**` to HWPX bold runs.

4. **Validate**
   - Re-open the packed HWPX as ZIP.
   - Parse key XML files as UTF-8.
   - Check `content.hpf` manifest/spine consistency.
   - Check `header.xml` style references used by sections.
   - Check Korean text is not garbled.
   - Check no stray `**`, stale `lineSegArray`, empty bullets, or missing assets remain.

## Bundled Scripts

Run commands from the skill directory unless a command says otherwise.

- `scripts/inspect_hwpx.py`: inspect HWPX package structure and write `template_inspection.md` / `template_structure.json`.
- `scripts/build_slot_map_draft.py`: create a first-pass slot map from an inspection result.
- `scripts/compile_from_slot_map.py`: compile report JSON into a template using a reviewed slot map.
- `scripts/create_hwpx_report.py`: create or validate an HWPX report with template-preserving helpers.
- `profiles/distribution_onepager.profile.json`: public-safe one-page report profile.
- `profiles/distribution_multipage.profile.json`: public-safe multi-page report profile.
- `profiles/distribution_longform.profile.json`: public-safe long-form report profile.
- `profiles/profile.schema.json`: local profile contract documentation.
- `templates/`: bundled public-safe HWPX report templates referenced by the distribution profiles.

Examples:

```powershell
python scripts/inspect_hwpx.py "C:\path\to\template.hwpx" --out-dir output\candidate_inspection
python scripts/build_slot_map_draft.py output\candidate_inspection\template_structure.json --out-dir output\candidate_slot_map
python scripts/compile_from_slot_map.py --input examples\public_ai_adoption_report.json --slot-map examples\slot_map_reviewed.example.json --output output\report.hwpx
python scripts/create_hwpx_report.py --validate-only output\report.hwpx
```

## References

Load only what is needed:

- `references/hwpx-structure-notes.md`: HWPX package/XML structure details.
- `references/public-report-writing-rules.md`: Korean public-sector report writing rules.
- `references/rhwp-hop-notes.md`: notes for editor-level HWPX/HWP automation choices.
- `references/verbatim-authoring.md`: preserving exact wording and avoiding unintended rewriting.
- `schemas/slot_map.schema.json`: reviewed slot map shape.

## Windows UTF-8 Bootstrap

Before running Python tools on Windows PowerShell, initialize UTF-8 output if your environment provides a bootstrap script.

Fallback:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; chcp 65001 > $null
```

## Done When

- The final artifact is an `.hwpx` file.
- Requested placeholders, report sections, tables, or slots are filled.
- Existing styles, table geometry, package manifest, and assets are preserved unless explicitly changed.
- `Contents/section*.xml` passes UTF-8 Korean text verification.
- Any skipped validation, unresolved slot-map review, or layout risk is reported clearly.
