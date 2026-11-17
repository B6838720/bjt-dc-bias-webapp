import unittest

from dc_bias import (
    REGION_ACTIVE,
    REGION_CUTOFF,
    REGION_SATURATION,
    calculate,
    calculate_fixed,
    calculate_emitter,
)

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

    def test_ic_increases_with_beta(self):
        # Spec 6.7 item 2: monotonic sanity independent of the reference numbers.
        low = calculate(**dict(REFERENCE, beta=50.0))
        high = calculate(**dict(REFERENCE, beta=200.0))
        self.assertGreater(high["ic"], low["ic"])


class TestValidation(unittest.TestCase):
    def test_zero_resistor_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=0.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)

    def test_zero_beta_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=0.0, vbe=0.70)

    def test_vbe_not_below_vcc_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=0.5, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)

    def test_zero_divider_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=0.0, r2=0.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)

    def test_overflowing_inputs_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=1e308, r2=1e308, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)


class TestRegions(unittest.TestCase):
    def test_cutoff_reports_physical_values(self):
        r = calculate(vcc=12.0, r1=100_000.0, r2=5_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(r["region"], REGION_CUTOFF)
        self.assertFalse(r["model_applies"])
        self.assertEqual(r["ic"], 0.0)
        self.assertEqual(r["ie"], 0.0)
        self.assertEqual(r["ib"], 0.0)
        self.assertEqual(r["ve"], 0.0)
        self.assertAlmostEqual(r["vc"], 12.0, places=6)
        self.assertAlmostEqual(r["vce"], 12.0, places=6)
        self.assertAlmostEqual(r["vb"], r["vth"], places=6)
        self.assertTrue(r["warnings"])

    def test_saturation_detected(self):
        r = calculate(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=100_000.0,
                      re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(r["region"], REGION_SATURATION)
        self.assertFalse(r["model_applies"])
        self.assertLess(r["vce"], 0.3)
        self.assertTrue(r["warnings"])

    def test_fractional_beta_accepted(self):
        r = calculate(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.5, vbe=0.70)
        self.assertGreater(r["ic"], 0.0)


class TestFixedAndEmitter(unittest.TestCase):
    def test_fixed_reference(self):
        r = calculate_fixed(vcc=12.0, rb=1e6, rc=2200.0, beta=100.0, vbe=0.70)
        self.assertAlmostEqual(r["ib"] * 1e6, 11.30, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.1300, places=3)
        self.assertAlmostEqual(r["ve"], 0.0, places=6)
        self.assertAlmostEqual(r["vb"], 0.70, places=6)
        self.assertAlmostEqual(r["vc"], 9.5140, places=3)
        self.assertAlmostEqual(r["vce"], 9.5140, places=3)
        self.assertEqual(r["region"], REGION_ACTIVE)
        self.assertEqual(r["warnings"], [])

    def test_emitter_reference(self):
        r = calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=1000.0,
                              beta=100.0, vbe=0.70)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.0263, places=3)
        self.assertAlmostEqual(r["ve"], 1.0366, places=3)
        self.assertAlmostEqual(r["vb"], 1.7366, places=3)
        self.assertAlmostEqual(r["vce"], 8.7054, places=3)

    def test_larger_re_reduces_ic(self):
        a = calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=1000.0,
                              beta=100.0, vbe=0.70)
        b = calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=2000.0,
                              beta=100.0, vbe=0.70)
        self.assertAlmostEqual(b["ic"] * 1e3, 0.9401, places=3)
        self.assertLess(b["ic"], a["ic"])

    def test_nonpositive_rb_rejected(self):
        with self.assertRaises(ValueError):
            calculate_fixed(vcc=12.0, rb=0.0, rc=2200.0, beta=100.0, vbe=0.70)

    def test_nonpositive_re_rejected(self):
        with self.assertRaises(ValueError):
            calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=0.0,
                              beta=100.0, vbe=0.70)
