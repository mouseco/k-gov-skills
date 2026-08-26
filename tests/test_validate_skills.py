import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", MODULE_PATH)
validate_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_skills)


class RepositoryContractTests(unittest.TestCase):
    def make_repository(self, root: Path, readme: str):
        skills = root / "skills"
        (skills / "alpha").mkdir(parents=True)
        (skills / "beta").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / "README.md").write_text(readme, encoding="utf-8")
        (root / "LICENSE").write_text("MIT", encoding="utf-8")
        (root / "llms.txt").write_text("agent summary", encoding="utf-8")
        (root / "docs" / "install.md").write_text("install", encoding="utf-8")
        (root / ".github" / "workflows" / "validate.yml").write_text("name: test", encoding="utf-8")
        return skills

    def test_repository_contract_accepts_matching_skill_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills = self.make_repository(
                root,
                "`alpha` `beta` ![count](Agent%20Skills-2-blue)",
            )
            errors = []
            with patch.multiple(
                validate_skills,
                ROOT=root,
                SKILLS=skills,
                README=root / "README.md",
                LICENSE=root / "LICENSE",
                LLMS=root / "llms.txt",
                INSTALL_GUIDE=root / "docs" / "install.md",
                CI_WORKFLOW=root / ".github" / "workflows" / "validate.yml",
            ):
                validate_skills.validate_repository_contract(errors)
            self.assertEqual([], errors)

    def test_repository_contract_rejects_missing_skill_in_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills = self.make_repository(
                root,
                "`alpha` ![count](Agent%20Skills-2-blue)",
            )
            errors = []
            with patch.multiple(
                validate_skills,
                ROOT=root,
                SKILLS=skills,
                README=root / "README.md",
                LICENSE=root / "LICENSE",
                LLMS=root / "llms.txt",
                INSTALL_GUIDE=root / "docs" / "install.md",
                CI_WORKFLOW=root / ".github" / "workflows" / "validate.yml",
            ):
                validate_skills.validate_repository_contract(errors)
            self.assertTrue(any("`beta`" in error for error in errors))


class TextHygieneTests(unittest.TestCase):
    def test_invalid_control_character_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bad.md").write_text("python scripts" + chr(11) + "alidate.py", encoding="utf-8")
            errors = []
            with patch.object(validate_skills, "ROOT", root):
                validate_skills.validate_text_hygiene(errors)
            self.assertTrue(any("U+000B" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
