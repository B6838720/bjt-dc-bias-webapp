import unittest
from unittest.mock import patch

import spice_engine
from app import DEFAULT_SIM_FORM, app


def fake_result(analysis="dc", **overrides):
    result = {
        "status": "success",
        "engine": "ngspice",
        "analysis": analysis,
        "analysis_label": spice_engine.ANALYSIS_LABELS[analysis],
        "model_name": "QNPN",
        "model_source": "test",
        "provenance": "ngspice batch log (-o) parsed by spice_engine.py",
        "values": {
            "VB": 1.942,
            "VE": 1.242,
            "VC": 9.294,
            "VCE": 8.052,
            "IC": 0.001230,
        },
        "series": [],
        "derived": ["IC = (VCC - VC) / RC"],
        "warnings": ["ผล DC มาจาก ngspice .op"],
        "log_excerpt": "Node Voltage ...",
        "netlist": "VCC vcc 0 DC 0\n.op\n.end",
    }
    result.update(overrides)
    return result


def sim_form(**overrides):
    data = dict(DEFAULT_SIM_FORM)
    data.update(overrides)
    return data


class TestSimulatorPage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_has_analysis_selector(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('name="analysis"', body)
        self.assertIn("DC · .op", body)
        self.assertIn("Transient · .tran", body)

    def test_get_analysis_is_respected(self):
        body = self.client.get("/?analysis=ac").get_data(as_text=True)
        self.assertIn('value="ac" selected', body)

    @patch("app.spice_engine.simulate")
    def test_simulate_route_shows_spice_result(self, mock_simulate):
        mock_simulate.return_value = fake_result()
        body = self.client.post("/simulate", data=sim_form()).get_data(as_text=True)
        self.assertIn("✓ ngspice", body)
        self.assertIn("DC Operating Point (.op)", body)
        self.assertIn("1.230 mA", body)
        self.assertIn("QNPN", body)
        self.assertIn("Analytical Reference", body)

    @patch("app.spice_engine.simulate")
    def test_amplitude_is_converted_from_mv_to_v(self, mock_simulate):
        mock_simulate.return_value = fake_result()
        self.client.post("/simulate", data=sim_form(sim_amp="20", sim_freq="2000"))
        params = mock_simulate.call_args.args[0]
        self.assertAlmostEqual(params.amp, 0.020, places=6)
        self.assertAlmostEqual(params.freq, 2000.0, places=3)

    @patch("app.spice_engine.simulate")
    def test_engine_error_shows_error_and_no_stale_success(self, mock_simulate):
        mock_simulate.side_effect = spice_engine.SimulationError("RE ต้องมากกว่า 0")
        body = self.client.post("/simulate", data=sim_form(sim_re="0")).get_data(as_text=True)
        self.assertIn("Simulation Error", body)
        self.assertIn("RE ต้องมากกว่า 0", body)
        self.assertNotIn("✓ ngspice", body)

    @patch("app.spice_engine.simulate")
    def test_invalid_form_does_not_call_engine(self, mock_simulate):
        body = self.client.post(
            "/simulate", data=sim_form(sim_vcc="abc")
        ).get_data(as_text=True)
        self.assertIn("กรุณากรอก VCC เป็นตัวเลข", body)
        mock_simulate.assert_not_called()

    @patch("app.spice_engine.simulate")
    def test_ac_chart_uses_returned_series(self, mock_simulate):
        mock_simulate.return_value = fake_result(
            analysis="ac",
            values={
                "PeakGain_dB": -2.0,
                "GainAt1k_dB": -2.0,
                "Cutoff_Hz": None,
            },
            series=[
                {"freq_hz": 1.0, "gain_db": -20.0, "phase_deg": 170.0},
                {"freq_hz": 1000.0, "gain_db": -2.0, "phase_deg": -10.0},
            ],
        )
        body = self.client.post(
            "/simulate", data=sim_form(analysis="ac")
        ).get_data(as_text=True)
        self.assertIn("Gain magnitude", body)
        self.assertIn("Phase (°) · Frequency", body)
        self.assertIn("not determined in sweep range", body)
        self.assertIn("polyline", body)


if __name__ == "__main__":
    unittest.main()
