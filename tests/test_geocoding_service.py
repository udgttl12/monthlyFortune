import unittest

from app.services.geocoding_service import GeocodingService


class GeocodingServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GeocodingService()

    def test_busan_aliases_resolve_to_same_coordinates(self) -> None:
        labels = ["Busan", "Busan-si", "부산"]
        resolved = [self.service.resolve(city=label, country_code="KR") for label in labels]

        for location in resolved:
            self.assertEqual(location.timezone, "Asia/Seoul")
            self.assertAlmostEqual(location.latitude, 35.1796, places=4)
            self.assertAlmostEqual(location.longitude, 129.0756, places=4)

        self.assertEqual({location.resolved_name for location in resolved}, {"Busan, South Korea"})

    def test_major_korean_regions_resolve_without_external_lookup(self) -> None:
        expected_locations = {
            "서울": ("Seoul, South Korea", 37.5665, 126.9780),
            "인천": ("Incheon, South Korea", 37.4563, 126.7052),
            "대구": ("Daegu, South Korea", 35.8714, 128.6014),
            "대전": ("Daejeon, South Korea", 36.3504, 127.3845),
            "광주": ("Gwangju, South Korea", 35.1595, 126.8526),
            "울산": ("Ulsan, South Korea", 35.5384, 129.3114),
            "제주": ("Jeju, South Korea", 33.4996, 126.5312),
            "강릉": ("Gangneung, South Korea", 37.7519, 128.8761),
            "전주": ("Jeonju, South Korea", 35.8242, 127.1480),
        }

        for city, (name, latitude, longitude) in expected_locations.items():
            with self.subTest(city=city):
                location = self.service.resolve(city=city, country_code="KR")

                self.assertEqual(location.resolved_name, name)
                self.assertEqual(location.timezone, "Asia/Seoul")
                self.assertAlmostEqual(location.latitude, latitude, places=4)
                self.assertAlmostEqual(location.longitude, longitude, places=4)
