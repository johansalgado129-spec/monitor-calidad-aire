import unittest

from backend.src.aqi import (
    calculate_pm25_aqi,
    calculate_no2_aqi,
    calculate_o3_aqi,
    aqi_category,
    to_ppb,
    to_ppm,
    who_comparison,
)


class TestAQI(unittest.TestCase):
    def test_pm25_good_upper_limit(self):
        self.assertEqual(calculate_pm25_aqi(9.0), 50)

    def test_pm25_moderate_upper_limit(self):
        self.assertEqual(calculate_pm25_aqi(35.4), 100)

    def test_no2_good_upper_limit(self):
        self.assertEqual(calculate_no2_aqi(53), 50)

    def test_no2_unhealthy_for_sensitive(self):
        value = calculate_no2_aqi(101)
        self.assertEqual(value, 101)

    def test_o3_good_upper_limit(self):
        self.assertEqual(calculate_o3_aqi(0.054), 50)

    def test_category(self):
        self.assertEqual(aqi_category(80)["categoria"], "Moderada")
        self.assertEqual(aqi_category(180)["categoria"], "Insalubre")

    def test_who_pm25(self):
        result = who_comparison("pm25", 20)
        self.assertTrue(result["supera_guia"])

    def test_conversion_no2_ugm3_to_ppb(self):
        # Aproximadamente 46.0055 ug/m3 = 24.45 ppb a 25 C y 1 atm.
        value = to_ppb("no2", 46.0055, "ug/m3")
        self.assertAlmostEqual(value, 24.45, places=2)

    def test_conversion_o3_ppb_to_ppm(self):
        self.assertAlmostEqual(to_ppm("o3", 70, "ppb"), 0.070, places=3)


if __name__ == "__main__":
    unittest.main()
