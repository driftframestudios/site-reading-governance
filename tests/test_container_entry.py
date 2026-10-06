"""Exercise the native governance pair validation used by the finite entry."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))
spec = importlib.util.spec_from_file_location("finite_governance_entry", ROOT / "infra/container_entry.py")
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
from container_runtime import publish


class GovernanceEntryTests(unittest.TestCase):
    def test_native_pairs_publish_material_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = publish(entry.produce, root)
            payload = root / result["directory"] / "payload"
            self.assertEqual({p.name for p in payload.iterdir()}, {"validation.json"})
            document = json.loads((payload / "validation.json").read_bytes())
            self.assertEqual(document["status"], "passed")
            self.assertEqual(len(document["pairs"]), 2)

    def test_native_rejection_prevents_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(entry, "validate_pair", return_value=["rejected-pair-fixture"]):
                with self.assertRaises(ValueError):
                    publish(entry.produce, root)
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
