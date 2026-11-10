import unittest

from dc_bias import REGION_ACTIVE, calculate

REFERENCE = dict(
    vcc=12.0, r1=100_000.0, r2=22_000.0,
    rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
)


class TestReferenceOperatingPoint(unittest.TestCase):
    def test_reference_operating_point(self):
        r = calculate(**REFERENCE)
        self.assertAlmostEqual(r["vth"], 2.1639, places=3)
        self.assertAlmostEqual(r["rth"], 18_032.79, places=1)
        self.assertAlmostEqual(r["ib"] * 1e6, 12.298, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.2298, places=3)
        self.assertAlmostEqual(r["ie"] * 1e3, 1.2421, places=3)
        self.assertAlmostEqual(r["vb"], 1.9421, places=3)
        self.assertAlmostEqual(r["ve"], 1.2421, places=3)
        self.assertAlmostEqual(r["vc"], 9.2943, places=3)
        self.assertAlmostEqual(r["vce"], 8.0522, places=3)
        self.assertEqual(r["region"], REGION_ACTIVE)
        self.assertTrue(r["model_applies"])
        self.assertEqual(r["warnings"], [])
