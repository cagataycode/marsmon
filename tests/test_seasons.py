"""Checks for the Mars season maths. Run with: python3 -m unittest discover tests"""
import datetime as dt
import unittest

from marsmon import seasons


def utc(s):
    return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)


class SeasonTests(unittest.TestCase):
    def test_known_year_starts(self):
        # Mars Year boundaries (Ls = 0) from the Clancy et al. calendar.
        for day, my in [("2022-12-26T12:00", 37), ("2024-11-12T12:00", 38), ("2026-09-30T12:00", 39)]:
            t = utc(day)
            self.assertEqual(seasons.mars_year(t), my)
            lon = seasons.ls(t)
            self.assertTrue(lon < 1.0 or lon > 359.0, f"{day}: Ls {lon:.2f}")

    def test_landing_seasons(self):
        # Perseverance landed at Ls ~5 of MY36; Curiosity at Ls ~150 of MY31.
        self.assertAlmostEqual(seasons.ls(utc("2021-02-18T20:55")), 5.2, delta=0.5)
        self.assertEqual(seasons.mars_year(utc("2021-02-18T20:55")), 36)
        self.assertAlmostEqual(seasons.ls(utc("2012-08-06T05:18")), 150.7, delta=0.5)
        self.assertEqual(seasons.mars_year(utc("2012-08-06T05:18")), 31)

    def test_sol_clock(self):
        # SkyCam frame WSM_2032_0847320424...: sol 2032 at 09:50:19 LMST, taken 2026-11-07T11:12:25 UTC.
        t = seasons.sol_to_utc("m20", 2032 + (9 + 50 / 60 + 19 / 3600) / 24)
        self.assertLess(abs((t - utc("2026-11-07T11:12:25")).total_seconds()), 30 * 60)
        # Curiosity Navcam NLB_848652377...: sol 5082 at 14:42:02 LMST, taken 2026-11-22T21:59:27 UTC.
        t = seasons.sol_to_utc("msl", 5082 + (14 + 42 / 60 + 2 / 3600) / 24)
        self.assertLess(abs((t - utc("2026-11-22T21:59:27")).total_seconds()), 30 * 60)


if __name__ == "__main__":
    unittest.main()
