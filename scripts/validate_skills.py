import json
import py_compile
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
FEATURES = ROOT / "docs" / "features"

SENSITIVE_PATTERNS = [
    "mouseco@",
    "@kosaf.go.kr",
    "김성진",
    "성진",
    "password",
    "api_key",
    "secret",
    "token",
]

IGNORE_PARTS = {".git", "tmp", "__pycache__"}
IGNORE_PATH_SNIPPETS = ["test-fixtures/private"]


def fail(errors, message):
    errors.append(message)


def parse_frontmatter(path: Path, errors):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        fail(errors, f"{path}: missing YAML frontmatter")
        return {}
    fm = m.group(1)
    data = {}
    current = None
    for line in fm.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current = key.strip()
            data[current] = value.strip().strip('"')
        elif current == "metadata" and ":" in line:
            key, value = line.split(":", 1)
            data[f"metadata.{key.strip()}"] = value.strip().strip('"')
    return data


def validate_skill_metadata(errors):
    if not SKILLS.exists():
        fail(errors, "skills directory missing")
        return
    for skill in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        skill_md = skill / "SKILL.md"
        if not skill_md.exists():
            fail(errors, f"{skill}: missing SKILL.md")
            continue
        data = parse_frontmatter(skill_md, errors)
        for key in ["name", "description", "license", "metadata.category", "metadata.locale", "metadata.phase"]:
            if not data.get(key):
                fail(errors, f"{skill_md}: missing {key}")
        if data.get("name") and data["name"] != skill.name:
            fail(errors, f"{skill_md}: name does not match directory ({data['name']} != {skill.name})")
        feature_doc = FEATURES / f"{skill.name}.md"
        if not feature_doc.exists():
            fail(errors, f"missing feature doc: {feature_doc}")


def validate_json(errors):
    for path in ROOT.rglob("*.json"):
        if any(part in IGNORE_PARTS for part in path.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"{path}: JSON parse failed: {exc}")


def validate_python(errors):
    for path in ROOT.rglob("*.py"):
        if any(part in IGNORE_PARTS for part in path.parts):
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            fail(errors, f"{path}: python compile failed: {exc}")


def validate_hwpx(errors):
    required = {"mimetype", "Contents/header.xml", "Contents/content.hpf"}
    for path in (SKILLS / "hwpx-mouseco" / "templates").glob("*.hwpx"):
        try:
            with zipfile.ZipFile(path) as zf:
                names = set(zf.namelist())
                missing = required - names
                if missing:
                    fail(errors, f"{path}: missing HWPX entries {sorted(missing)}")
                for xml_name in [n for n in names if n.endswith(".xml") or n.endswith(".hpf")]:
                    try:
                        ET.fromstring(zf.read(xml_name))
                    except Exception as exc:
                        fail(errors, f"{path}:{xml_name}: XML parse failed: {exc}")
        except Exception as exc:
            fail(errors, f"{path}: invalid HWPX zip: {exc}")


def validate_public_safety(errors):
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        normalized = str(path.relative_to(ROOT)).replace("\\", "/")
        if any(part in IGNORE_PARTS for part in path.parts):
            continue
        if any(snippet in normalized for snippet in IGNORE_PATH_SNIPPETS):
            continue
        if path.suffix.lower() in {".hwpx", ".png", ".jpg", ".jpeg", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SENSITIVE_PATTERNS:
            if pattern.lower() in text.lower():
                # Allow documentation that names the pattern as a rule, not as secret content,
                # and allow ordinary code identifiers such as title_tokens.
                allowed_rule_docs = {
                    ".gitignore",
                    "README.md",
                    "docs/adding-a-skill.md",
                    "docs/security-and-secrets.md",
                    "scripts/validate_skills.py",
                }
                if normalized in allowed_rule_docs:
                    continue
                # kosis-stats documents and code intentionally mention generic API-key
                # and secret-resolution variable names. They must not contain actual key values.
                if normalized.startswith("skills/kosis-stats/") or normalized == "docs/features/kosis-stats.md":
                    if pattern in {"password", "api_key", "secret"}:
                        continue
                if normalized.startswith("skills/public-data-finder/") or normalized == "docs/features/public-data-finder.md":
                    if pattern in {"api_key", "secret"}:
                        continue
                if pattern == "token" and path.suffix.lower() in {".py", ".md"}:
                    continue
                fail(errors, f"{path}: possible sensitive pattern {pattern!r}")


def main():
    errors = []
    validate_skill_metadata(errors)
    validate_json(errors)
    validate_python(errors)
    validate_hwpx(errors)
    validate_public_safety(errors)
    if errors:
        print("FAIL")
        for err in errors:
            print(f"- {err}")
        return 1
    print("OK: skill metadata, feature docs, JSON, Python, HWPX, and public-safety checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
