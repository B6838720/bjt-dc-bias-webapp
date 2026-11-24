import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace

import spice_engine


MODEL_CARD = ".model QNPN NPN(Is=1e-14 VAF=100 Beta=100)"


def make_params(analysis="dc", **overrides):
    values = dict(
        analysis=analysis,
        vcc=12.0,
        r1=100_000.0,
        r2=22_000.0,
        rc=2_200.0,
        re=1_000.0,
        rl=10_000.0,
        cin=10e-6,
        cout=10e-6,
        amp=0.01,
        freq=1_000.0,
        beta=100.0,
        vbe=0.70,
        fstart=1.0,
        fstop=10_000_000.0,
        fpoints=20,
        tstep=1e-6,
        tstop=0.005,
        model_name="QNPN",
        model_text=MODEL_CARD,
        model_source="test",
    )
    values.update(overrides)
    return spice_engine.SimulationInput(**values)


def fake_runner(log_text, calls=None, returncode=0):
    calls = calls if calls is not None else []

    def runner(command, cwd, **kwargs):
        calls.append(command)
        Path(cwd, "run.log").write_text(log_text, encoding="utf-8")
        return SimpleNamespace(returncode=returncode, stdout="", stderr="")

    return runner


class TestNetlistBuilder(unittest.TestCase):
    def test_dc_netlist_has_op_only(self):
        netlist = spice_engine.build_netlist(make_params("dc"))
        self.assertIn(".op", netlist)
        self.assertNotIn(".ac ", netlist)
        self.assertNotIn(".tran", netlist)
        self.assertIn("Q1 collector base emitter QNPN", netlist)
        self.assertIn("VCC vcc 0 DC 12", netlist)
        self.assertIn(MODEL_CARD, netlist)

    def test_ac_netlist_has_sweep_and_print(self):
        netlist = spice_engine.build_netlist(make_params("ac"))
        self.assertIn(".ac DEC 20 1 10000000", netlist)
        self.assertIn(".print ac vdb(output) vdb(input) vp(output) vp(input)", netlist)
        self.assertNotIn(".op", netlist)

    def test_tran_netlist_has_tran_and_print(self):
        netlist = spice_engine.build_netlist(make_params("transient"))
        self.assertIn(".tran 1e-06 0.005", netlist)
        self.assertIn(".print tran v(input) v(output)", netlist)
        self.assertNotIn(".ac ", netlist)

    def test_build_command_is_argv_list(self):
        command = spice_engine.build_command(
            "ngspice", Path("circuit.cir"), Path("run.log")
        )
        self.assertEqual(command[:2], ["ngspice", "-b"])
        self.assertIsInstance(command, list)
        self.assertNotIn("shell=True", command)

    def test_model_card_cannot_inject_analysis(self):
        params = make_params(model_text=MODEL_CARD + "\n.control\n.endc")
        with self.assertRaises(spice_engine.SimulationError):
            spice_engine.build_netlist(params)


class TestValidation(unittest.TestCase):
    def test_zero_re_rejected(self):
        with self.assertRaises(spice_engine.SimulationError):
            spice_engine.validate_params(make_params(re=0.0))

    def test_missing_model_rejected(self):
        with self.assertRaises(spice_engine.SimulationError):
            spice_engine.validate_params(make_params(model_name=""))

    def test_bad_frequency_range_rejected(self):
        with self.assertRaises(spice_engine.SimulationError):
            spice_engine.validate_params(make_params(fstart=100.0, fstop=10.0))


class TestParsers(unittest.TestCase):
    def test_parse_dc_log_derives_vce_and_ic(self):
        log = """Node        Voltage
--------    -------
vcc         1.200000e+01
base        1.942000e+00
emitter     1.242000e+00
collector   9.294000e+00
"""
        parsed = spice_engine.parse_dc_log(log, make_params("dc"))
        self.assertAlmostEqual(parsed["values"]["VB"], 1.942, places=3)
        self.assertAlmostEqual(parsed["values"]["VCE"], 8.052, places=3)
        self.assertAlmostEqual(parsed["values"]["IC"], 0.001230, places=6)
        self.assertTrue(any("IC =" in item for item in parsed["derived"]))

    def test_parse_ac_log_computes_gain_and_phase(self):
        log = """1.000000e+00 -2.000000e+01 -2.000000e+00 2.967030e+00 3.054326e+00
1.000000e+03 -4.000000e+00 -2.000000e+00 -1.745329e-01 0.000000e+00
"""
        parsed = spice_engine.parse_ac_log(log)
        self.assertAlmostEqual(parsed["values"]["PeakGain_dB"], -2.0, places=3)
        self.assertAlmostEqual(parsed["values"]["GainAt1k_dB"], -2.0, places=3)
        self.assertEqual(len(parsed["series"]), 2)
        self.assertAlmostEqual(parsed["series"][1]["phase_deg"], -10.0, places=3)
        self.assertIsNotNone(parsed["values"]["Cutoff_Hz"])
        self.assertAlmostEqual(parsed["values"]["Cutoff_Hz"], 273.842, places=2)

    def test_parse_ac_log_joins_real_ngspice_split_tables(self):
        log = """Index   frequency       vdb(output)     vdb(input)
0       1.000000e+00    -4.000000e+01   -4.000000e+01
1       1.000000e+03    -3.500000e+01   -4.000000e+01
Index   frequency       vp(output)      vp(input)
0       1.000000e+00    -1.000000e+00   0.000000e+00
1       1.000000e+03    -3.141593e+00   0.000000e+00
"""
        parsed = spice_engine.parse_ac_log(log)
        self.assertEqual(len(parsed["series"]), 2)
        self.assertAlmostEqual(parsed["values"]["GainAt1k_dB"], 5.0, places=3)
        self.assertAlmostEqual(parsed["series"][1]["phase_deg"], -180.0, places=3)

    def test_parse_tran_log_strips_ngspice_index(self):
        log = """Index   time            v(input)        v(output)
0       0.000000e+00    0.000000e+00    0.000000e+00
1       1.000000e-03    1.000000e-02   -5.000000e-02
2       2.000000e-03    0.000000e+00    0.000000e+00
"""
        parsed = spice_engine.parse_tran_log(log)
        self.assertAlmostEqual(parsed["values"]["TimeEnd_s"], 0.002, places=6)
        self.assertAlmostEqual(parsed["values"]["VinPeak_V"], 0.01, places=4)

    def test_parse_tran_log_detects_inversion(self):
        log = """0.000000e+00 1.000000e-02 -5.000000e-02
1.000000e-03 0.000000e+00 0.000000e+00
2.000000e-03 -1.000000e-02 5.000000e-02
"""
        parsed = spice_engine.parse_tran_log(log)
        self.assertEqual(parsed["values"]["PhaseRelation"], "inverted")
        self.assertAlmostEqual(parsed["values"]["VinPeak_V"], 0.01, places=4)
        self.assertAlmostEqual(parsed["values"]["VoutPeak_V"], 0.05, places=4)


class TestSimulateWithFakeRunner(unittest.TestCase):
    def test_simulate_success_uses_real_log_shape(self):
        log = """Node        Voltage
vcc         1.200000e+01
base        1.942000e+00
emitter     1.242000e+00
collector   9.294000e+00
"""
        calls = []
        result = spice_engine.simulate(
            make_params("dc"),
            engine="ngspice",
            runner=fake_runner(log, calls),
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["engine"], "ngspice")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "ngspice")
        self.assertAlmostEqual(result["values"]["IC"], 0.001230, places=6)

    def test_simulate_failed_run_raises(self):
        with self.assertRaises(spice_engine.SimulationError):
            spice_engine.simulate(
                make_params("dc"),
                runner=fake_runner("fatal error: model not found", returncode=1),
            )

    def test_timeout_is_forwarded_as_error(self):
        def timeout_runner(command, cwd, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 30))

        with self.assertRaises(spice_engine.SimulationError):
            spice_engine.simulate(make_params("dc"), runner=timeout_runner)


if __name__ == "__main__":
    unittest.main()
