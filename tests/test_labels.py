"""Checks for the label store behind the labelling page."""
import json
import tempfile
import unittest
from pathlib import Path

from marsmon import questions
from marsmon.label_server import Store


class LabelStoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        d = Path(self.dir.name)
        (d / "sample.json").write_text(json.dumps({"items": [{"imageid": "A"}, {"imageid": "B"}]}))
        self.labels = d / "labels.json"
        self.store = Store(d / "sample.json", self.labels)

    def tearDown(self):
        self.dir.cleanup()

    def test_saves_and_keeps_other_entries(self):
        self.store.save("A", {"ground_visible": "yes", "main_terrain": "sand_ripples", "layering": "no", "steep_slope": "unsure"}, "")
        self.store.save("B", {"ground_visible": "no", "main_terrain": "n/a", "layering": "n/a", "steep_slope": "n/a"}, " deck ")
        saved = json.loads(self.labels.read_text())
        self.assertEqual(set(saved), {"A", "B"})
        self.assertEqual(saved["A"]["answers"]["main_terrain"], "sand_ripples")
        self.assertEqual(saved["B"]["note"], "deck")
        self.assertEqual(saved["A"]["questions_version"], questions.VERSION)

    def test_rejects_bad_input(self):
        good = {"ground_visible": "yes", "main_terrain": "flat_bedrock", "layering": "no", "steep_slope": "no"}
        with self.assertRaises(ValueError):
            self.store.save("Z", good, "")  # not in the sample
        with self.assertRaises(ValueError):
            self.store.save("A", {**good, "main_terrain": "lava"}, "")
        with self.assertRaises(ValueError):
            self.store.save("A", {"ground_visible": "yes"}, "")  # missing answers
        with self.assertRaises(ValueError):
            self.store.save("A", {**good, "main_terrain": "n/a"}, "")  # n/a only when no ground
        with self.assertRaises(ValueError):
            self.store.save("A", {**good, "ground_visible": "no"}, "")  # no ground needs n/a elsewhere
        self.assertFalse(self.labels.exists())


if __name__ == "__main__":
    unittest.main()
