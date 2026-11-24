"""Sanity checks on data/sources.toml. Run: python3 -m unittest discover -s tests"""
import tomllib
import unittest
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / "data" / "sources.toml"
STATUSES = {"ready", "verify", "manual", "blocked"}
KINDS = {"git", "file", "manual"}
REQUIRED = {"id", "name", "language", "kind", "url", "format", "license", "license_url", "attribution", "status", "phase", "notes"}
PHASES = {1, 2}


class ManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with MANIFEST.open("rb") as fh:
            cls.sources = tomllib.load(fh)["source"]

    def test_required_fields_and_enums(self):
        for s in self.sources:
            self.assertFalse(REQUIRED - s.keys(), f"{s.get('id')} missing {REQUIRED - s.keys()}")
            self.assertIn(s["status"], STATUSES, s["id"])
            self.assertIn(s["kind"], KINDS, s["id"])
            self.assertIn(s["phase"], PHASES, s["id"])

    def test_ids_unique(self):
        ids = [s["id"] for s in self.sources]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ready_sources_are_fully_documented(self):
        for s in self.sources:
            if s["status"] == "ready":
                for key in ("url", "license_url", "attribution"):
                    self.assertTrue(s[key], f"{s['id']} is ready but has empty {key}")
                self.assertTrue(s["url"].startswith("https://"), s["id"])
                if s["kind"] == "file":
                    self.assertTrue(s.get("filename"), s["id"])

    def test_blocked_sources_have_no_url(self):
        for s in self.sources:
            if s["status"] == "blocked":
                self.assertEqual(s["url"], "", s["id"])


if __name__ == "__main__":
    unittest.main()
