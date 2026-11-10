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
