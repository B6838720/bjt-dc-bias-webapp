import unittest

from app import app

REFERENCE_FORM = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.70", "r_unit": "kohm",
}


class TestIndexPage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_returns_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="vcc"', body)
        self.assertIn('name="beta"', body)
        self.assertIn('name="r_unit"', body)


class TestCalculateRoute(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_calculate_shows_backend_results(self):
        response = self.client.post("/calculate", data=REFERENCE_FORM)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("1.230", body)   # IC = 1.230 mA จาก Python
        self.assertIn("8.052", body)   # VCE
        self.assertIn("Forward Active", body)

    def test_invalid_resistor_shows_error(self):
        data = dict(REFERENCE_FORM, r1="0")
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", response.get_data(as_text=True))

    def test_non_numeric_shows_error(self):
        data = dict(REFERENCE_FORM, vcc="abc")
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอก VCC เป็นตัวเลข", response.get_data(as_text=True))

    def test_empty_field_shows_error(self):
        data = dict(REFERENCE_FORM, vbe="")
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอก VBE", response.get_data(as_text=True))

    def test_cutoff_shows_zero_current(self):
        data = dict(REFERENCE_FORM, r2="5")
        response = self.client.post("/calculate", data=data)
        body = response.get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("0.000 mA", body)

    def test_divider_mode_keeps_old_result(self):
        response = self.client.post("/calculate", data=dict(REFERENCE_FORM, mode="divider"))
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("1.230", body)
        self.assertIn("8.052", body)

    def test_fixed_mode_uses_fixed_formula(self):
        data = {"mode": "fixed", "vcc": "12", "rb": "1000", "rc": "2.2",
                "beta": "100", "vbe": "0.70", "r_unit": "kohm"}
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("1.130", body)
        self.assertIn("9.514", body)

    def test_emitter_mode_uses_re(self):
        data = {"mode": "emitter", "vcc": "12", "rb": "1000", "rc": "2.2",
                "re": "1", "beta": "100", "vbe": "0.70", "r_unit": "kohm"}
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("1.026", body)
        self.assertIn("8.705", body)

    def test_unknown_mode_is_error(self):
        data = dict(REFERENCE_FORM, mode="bogus")
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("โหมดไม่รู้จัก", body)
        self.assertNotIn("1.230", body)

    def test_zero_rb_error_has_no_stale_result(self):
        data = {"mode": "fixed", "vcc": "12", "rb": "0", "rc": "2.2",
                "beta": "100", "vbe": "0.70", "r_unit": "kohm"}
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("RB ต้องมากกว่า 0", body)
        self.assertNotIn("9.514", body)

    def test_index_has_mode_selector(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('name="mode"', body)
        self.assertIn("เปลี่ยนโหมด", body)

    def test_get_fixed_mode_hides_divider_fields(self):
        body = self.client.get("/?mode=fixed").get_data(as_text=True)
        self.assertIn('name="rb"', body)
        self.assertNotIn('name="r1"', body)
        self.assertNotIn('name="re"', body)

    def test_get_emitter_mode_shows_re(self):
        body = self.client.get("/?mode=emitter").get_data(as_text=True)
        self.assertIn('name="rb"', body)
        self.assertIn('name="re"', body)
