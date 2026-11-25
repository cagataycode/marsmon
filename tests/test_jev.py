"""Checks for building Jev requests and reading answers (no network)."""
import json
import unittest

from marsmon import jev, questions
from marsmon.probe import _fake_jpeg


class JevRequestTests(unittest.TestCase):
    def test_request_references_its_image(self):
        payload, record = jev.build_request(_fake_jpeg(1200, 902))
        (ref,) = payload["assets"]
        self.assertEqual(payload["state"], {"photo": ref})
        self.assertEqual(set(payload["questions"]), {q["id"] for q in questions.TERRAIN})
        self.assertNotIn("data_base64", json.dumps(record))  # the log keeps a hash, not the image
        self.assertEqual(record["assets"][ref]["width"], 1200)

    def test_image_limits(self):
        with self.assertRaises(ValueError):
            jev.check_image(_fake_jpeg(200, 900))   # a side under 280 px
        with self.assertRaises(ValueError):
            jev.check_image(_fake_jpeg(2048, 2048))  # a side over 1568 px

    def test_answers_to_labels(self):
        ans = {"ground_visible": {"noul": 0.95}, "main_terrain": {"choice": "sand_ripples"},
               "layering": {"noul": 0.5}, "steep_slope": {"noul": 0.1}}
        self.assertEqual(jev.as_labels(ans), {"ground_visible": "yes", "main_terrain": "sand_ripples",
                                              "layering": "unsure", "steep_slope": "no"})
        ans["ground_visible"]["noul"] = 0.05
        self.assertEqual(jev.as_labels(ans)["main_terrain"], "n/a")


if __name__ == "__main__":
    unittest.main()
