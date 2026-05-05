# k-gov-skills

Korean public-sector AI skills and HWPX automation toolkit.

This repository collects reusable agent skills for Korean public-sector
documents, public data workflows, and HWPX automation.

## Skills

| Skill | Purpose |
| --- | --- |
| `hwpx-autofill-conversion` | Fill or rewrite `.hwpx` templates while preserving the original document structure and styles. |

## Install

Install a skill from this repository by pointing Codex skill installer at the
skill directory:

```text
$skill-installer install https://github.com/mouseco/k-gov-skills/tree/main/skills/hwpx-autofill-conversion
```

Restart Codex after installing a skill so it is picked up in new sessions.

## Repository Layout

```text
skills/
  <skill-name>/
    SKILL.md
    scripts/       optional deterministic helpers
    references/    optional detailed references
    profiles/      public-safe template writing profiles
    templates/     public-safe HWPX templates referenced by profiles
    assets/        optional public-safe templates or assets
```

## Public-Safe Publishing Rules

- Do not commit personal, client, school, government, or unpublished `.hwpx` files.
- Keep generated outputs, unpacked document folders, and temporary files out of git.
- Put only reusable, licensed, public-safe templates under `assets/` or `examples/`.
- Keep each skill's `SKILL.md` concise and move long format notes into `references/`.
