from pathlib import Path

from unittest import TestCase


class TestPhase1Isolation(TestCase):
	def test_cmr_source_does_not_reference_legacy_package(self):
		app_root = Path(__file__).resolve().parents[2]
		for path in app_root.rglob("*"):
			if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path.suffix in {".md", ".lock", ".pyc"}:
				continue
			legacy_package = "pipe_" + "laying_inhouse"
			self.assertNotIn(legacy_package, path.read_text(encoding="utf-8", errors="ignore"))

	def test_no_pwa_or_service_worker_in_version_one(self):
		app_root = Path(__file__).resolve().parents[2]
		filenames = {path.name.lower() for path in app_root.rglob("*") if path.is_file()}
		self.assertFalse(any("service-worker" in name or name.endswith("sw.js") for name in filenames))
