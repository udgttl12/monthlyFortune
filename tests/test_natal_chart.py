import unittest

from datetime import datetime
from fastapi.testclient import TestClient
from zoneinfo import ZoneInfo

from app.main import app
from app.schemas.chart import NatalChartRequest
from app.services.astrology_service import AstrologyService
from app.services.cache import TTLCache
from app.services.geocoding_service import GeocodingService
from app.services.natal_chart_engine import NatalChartEngine

SIGN_INDEX = {
    "Aries": 0,
    "Taurus": 1,
    "Gemini": 2,
    "Cancer": 3,
    "Leo": 4,
    "Virgo": 5,
    "Libra": 6,
    "Scorpio": 7,
    "Sagittarius": 8,
    "Capricorn": 9,
    "Aquarius": 10,
    "Pisces": 11,
}


def expected_longitude(sign: str, degree: int, minute: int) -> float:
    return (SIGN_INDEX[sign] * 30) + degree + (minute / 60)


def shortest_distance(first: float, second: float) -> float:
    return abs((first - second + 180) % 360 - 180)


REFERENCE_CASES = [
    {
        "id": "busan_sample",
        "city": "Busan",
        "birth_date": "1988-12-06",
        "birth_time": "19:59",
        "timezone": "Asia/Seoul",
        "latitude": 35.1796,
        "longitude": 129.0756,
        "expected_points": {
            "Sun": ("Sagittarius", 14, 33),
            "Moon": ("Scorpio", 11, 26),
            "Mercury": ("Sagittarius", 17, 22),
            "Venus": ("Scorpio", 15, 57),
            "Mars": ("Aries", 8, 32),
            "Jupiter": ("Taurus", 29, 16),
            "Saturn": ("Capricorn", 2, 36),
            "Uranus": ("Capricorn", 0, 13),
            "Neptune": ("Capricorn", 8, 59),
            "Pluto": ("Scorpio", 13, 45),
            "North Node": ("Pisces", 9, 8),
            "Lilith": ("Virgo", 22, 54),
            "Chiron": ("Cancer", 5, 30),
        },
        "expected_angles": {
            "asc": ("Cancer", 23, 27),
            "mc": ("Aries", 10, 5),
        },
        "expected_house_signs": [
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
        ],
    },
    {
        "id": "seoul_solstice",
        "city": "Seoul",
        "birth_date": "1990-06-21",
        "birth_time": "12:00",
        "timezone": "Asia/Seoul",
        "latitude": 37.5665,
        "longitude": 126.978,
        "expected_points": {
            "Sun": ("Gemini", 29, 30),
            "Moon": ("Gemini", 6, 7),
            "Mercury": ("Gemini", 16, 3),
            "Venus": ("Taurus", 25, 24),
            "Mars": ("Aries", 15, 4),
            "Jupiter": ("Cancer", 17, 7),
            "Saturn": ("Capricorn", 23, 41),
            "Uranus": ("Capricorn", 7, 57),
            "Neptune": ("Capricorn", 13, 34),
            "Pluto": ("Scorpio", 15, 18),
            "North Node": ("Aquarius", 9, 24),
            "Lilith": ("Scorpio", 25, 35),
            "Chiron": ("Cancer", 16, 38),
        },
        "expected_angles": {
            "asc": ("Virgo", 22, 40),
            "mc": ("Gemini", 21, 46),
        },
        "expected_house_signs": [
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
        ],
    },
    {
        "id": "incheon_y2k",
        "city": "Incheon",
        "birth_date": "2000-01-01",
        "birth_time": "00:00",
        "timezone": "Asia/Seoul",
        "latitude": 37.4563,
        "longitude": 126.7052,
        "expected_points": {
            "Sun": ("Capricorn", 9, 29),
            "Moon": ("Scorpio", 2, 44),
            "Mercury": ("Capricorn", 0, 32),
            "Venus": ("Sagittarius", 0, 30),
            "Mars": ("Aquarius", 27, 17),
            "Jupiter": ("Aries", 25, 13),
            "Saturn": ("Taurus", 10, 25),
            "Uranus": ("Aquarius", 14, 46),
            "Neptune": ("Aquarius", 3, 10),
            "Pluto": ("Sagittarius", 11, 25),
            "North Node": ("Leo", 5, 5),
            "Lilith": ("Sagittarius", 23, 22),
            "Chiron": ("Sagittarius", 11, 31),
        },
        "expected_angles": {
            "asc": ("Libra", 1, 4),
            "mc": ("Cancer", 1, 12),
        },
        "expected_house_signs": [
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
        ],
    },
    {
        "id": "daegu_late_summer",
        "city": "Daegu",
        "birth_date": "1977-08-16",
        "birth_time": "08:30",
        "timezone": "Asia/Seoul",
        "latitude": 35.8714,
        "longitude": 128.6014,
        "expected_points": {
            "Sun": ("Leo", 23, 0),
            "Moon": ("Virgo", 6, 1),
            "Mercury": ("Virgo", 18, 54),
            "Venus": ("Cancer", 15, 10),
            "Mars": ("Gemini", 19, 49),
            "Jupiter": ("Gemini", 29, 12),
            "Saturn": ("Leo", 20, 45),
            "Uranus": ("Scorpio", 8, 5),
            "Neptune": ("Sagittarius", 13, 24),
            "Pluto": ("Libra", 12, 13),
            "North Node": ("Libra", 17, 52),
            "Lilith": ("Gemini", 12, 41),
            "Chiron": ("Taurus", 5, 45),
        },
        "expected_angles": {
            "asc": ("Virgo", 26, 9),
            "mc": ("Gemini", 25, 44),
        },
        "expected_house_signs": [
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
        ],
    },
    {
        "id": "daejeon_equinox",
        "city": "Daejeon",
        "birth_date": "1985-03-20",
        "birth_time": "23:45",
        "timezone": "Asia/Seoul",
        "latitude": 36.3504,
        "longitude": 127.3845,
        "expected_points": {
            "Sun": ("Pisces", 29, 56),
            "Moon": ("Pisces", 20, 13),
            "Mercury": ("Aries", 17, 31),
            "Venus": ("Aries", 21, 20),
            "Mars": ("Taurus", 3, 55),
            "Jupiter": ("Aquarius", 8, 54),
            "Saturn": ("Scorpio", 27, 59),
            "Uranus": ("Sagittarius", 17, 59),
            "Neptune": ("Capricorn", 3, 33),
            "Pluto": ("Scorpio", 4, 15),
            "North Node": ("Taurus", 20, 59),
            "Lilith": ("Aries", 21, 53),
            "Chiron": ("Gemini", 4, 7),
        },
        "expected_angles": {
            "asc": ("Sagittarius", 2, 38),
            "mc": ("Virgo", 15, 34),
        },
        "expected_house_signs": [
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
        ],
    },
    {
        "id": "gwangju_winter_morning",
        "city": "Gwangju",
        "birth_date": "1995-12-25",
        "birth_time": "06:15",
        "timezone": "Asia/Seoul",
        "latitude": 35.1595,
        "longitude": 126.8526,
        "expected_points": {
            "Sun": ("Capricorn", 2, 35),
            "Moon": ("Aquarius", 12, 6),
            "Mercury": ("Capricorn", 19, 34),
            "Venus": ("Aquarius", 3, 51),
            "Mars": ("Capricorn", 18, 38),
            "Jupiter": ("Sagittarius", 27, 52),
            "Saturn": ("Pisces", 18, 57),
            "Uranus": ("Capricorn", 28, 57),
            "Neptune": ("Capricorn", 24, 25),
            "Pluto": ("Sagittarius", 1, 42),
            "North Node": ("Libra", 22, 49),
            "Lilith": ("Cancer", 9, 42),
            "Chiron": ("Libra", 13, 10),
        },
        "expected_angles": {
            "asc": ("Sagittarius", 13, 6),
            "mc": ("Virgo", 28, 24),
        },
        "expected_house_signs": [
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
        ],
    },
    {
        "id": "ulsan_historic_evening",
        "city": "Ulsan",
        "birth_date": "1969-07-20",
        "birth_time": "20:17",
        "timezone": "Asia/Seoul",
        "latitude": 35.5384,
        "longitude": 129.3114,
        "expected_points": {
            "Sun": ("Cancer", 27, 33),
            "Moon": ("Libra", 3, 7),
            "Mercury": ("Cancer", 25, 3),
            "Venus": ("Gemini", 14, 37),
            "Mars": ("Sagittarius", 2, 43),
            "Jupiter": ("Libra", 0, 41),
            "Saturn": ("Taurus", 8, 5),
            "Uranus": ("Libra", 0, 41),
            "Neptune": ("Scorpio", 26, 2),
            "Pluto": ("Virgo", 23, 0),
            "North Node": ("Pisces", 24, 0),
            "Lilith": ("Cancer", 14, 24),
            "Chiron": ("Aries", 6, 50),
        },
        "expected_angles": {
            "asc": ("Aquarius", 11, 13),
            "mc": ("Scorpio", 28, 51),
        },
        "expected_house_signs": [
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
        ],
    },
    {
        "id": "jeju_leap_day",
        "city": "Jeju",
        "birth_date": "2008-02-29",
        "birth_time": "13:05",
        "timezone": "Asia/Seoul",
        "latitude": 33.4996,
        "longitude": 126.5312,
        "expected_points": {
            "Sun": ("Pisces", 9, 57),
            "Moon": ("Sagittarius", 10, 45),
            "Mercury": ("Aquarius", 13, 4),
            "Venus": ("Aquarius", 14, 12),
            "Mars": ("Gemini", 28, 43),
            "Jupiter": ("Capricorn", 15, 27),
            "Saturn": ("Virgo", 4, 47),
            "Uranus": ("Pisces", 18, 9),
            "Neptune": ("Aquarius", 22, 24),
            "Pluto": ("Capricorn", 0, 51),
            "North Node": ("Aquarius", 27, 13),
            "Lilith": ("Scorpio", 25, 24),
            "Chiron": ("Aquarius", 17, 36),
        },
        "expected_angles": {
            "asc": ("Cancer", 2, 34),
            "mc": ("Pisces", 14, 56),
        },
        "expected_house_signs": [
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
        ],
    },
    {
        "id": "gangneung_venus_transit",
        "city": "Gangneung",
        "birth_date": "2012-06-06",
        "birth_time": "09:00",
        "timezone": "Asia/Seoul",
        "latitude": 37.7519,
        "longitude": 128.8761,
        "expected_points": {
            "Sun": ("Gemini", 15, 42),
            "Moon": ("Capricorn", 7, 4),
            "Mercury": ("Gemini", 27, 2),
            "Venus": ("Gemini", 15, 47),
            "Mars": ("Virgo", 16, 48),
            "Jupiter": ("Taurus", 28, 41),
            "Saturn": ("Libra", 23, 4),
            "Uranus": ("Aries", 7, 59),
            "Neptune": ("Pisces", 3, 9),
            "Pluto": ("Capricorn", 8, 50),
            "North Node": ("Sagittarius", 4, 40),
            "Lilith": ("Taurus", 19, 8),
            "Chiron": ("Pisces", 9, 44),
        },
        "expected_angles": {
            "asc": ("Leo", 6, 27),
            "mc": ("Aries", 25, 33),
        },
        "expected_house_signs": [
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
        ],
    },
    {
        "id": "jeonju_autumn_night",
        "city": "Jeonju",
        "birth_date": "2003-10-15",
        "birth_time": "22:10",
        "timezone": "Asia/Seoul",
        "latitude": 35.8242,
        "longitude": 127.148,
        "expected_points": {
            "Sun": ("Libra", 21, 46),
            "Moon": ("Gemini", 18, 52),
            "Mercury": ("Libra", 14, 45),
            "Venus": ("Scorpio", 7, 10),
            "Mars": ("Pisces", 2, 16),
            "Jupiter": ("Virgo", 10, 11),
            "Saturn": ("Cancer", 13, 8),
            "Uranus": ("Aquarius", 29, 8),
            "Neptune": ("Aquarius", 10, 25),
            "Pluto": ("Sagittarius", 17, 50),
            "North Node": ("Taurus", 21, 48),
            "Lilith": ("Taurus", 27, 24),
            "Chiron": ("Capricorn", 12, 52),
        },
        "expected_angles": {
            "asc": ("Cancer", 5, 54),
            "mc": ("Pisces", 17, 17),
        },
        "expected_house_signs": [
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
        ],
    },
]


class NatalChartGoldenTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AstrologyService(
            natal_chart_engine=NatalChartEngine(),
            geocoding_service=GeocodingService(cache=TTLCache(ttl_seconds=3600)),
            cache=TTLCache(ttl_seconds=3600),
        )
        self.request = NatalChartRequest(
            birthDate="1988-12-06",
            birthTime="19:59",
            city="Busan",
            countryCode="KR",
            timezone="Asia/Seoul",
        )
        self.response = self.service.build_natal_chart(self.request)
        self.point_map = {point.name: point for point in self.response.points}
        self.aspect_map = {
            (aspect.point_a, aspect.aspect, aspect.point_b): aspect for aspect in self.response.aspects
        }

    def test_major_planets_and_angles_match_sample(self) -> None:
        for name, sign, degree, minute, house in [
            ("Sun", "Sagittarius", 14, 33, 6),
            ("Moon", "Scorpio", 11, 26, 5),
            ("Mercury", "Sagittarius", 17, 21, 6),
            ("Venus", "Scorpio", 15, 57, 5),
            ("Mars", "Aries", 8, 31, 10),
            ("Jupiter", "Taurus", 29, 16, 11),
            ("Saturn", "Capricorn", 2, 35, 7),
            ("Uranus", "Capricorn", 0, 13, 7),
            ("Neptune", "Capricorn", 8, 58, 7),
            ("Pluto", "Scorpio", 13, 44, 5),
        ]:
            point = self.point_map[name]
            self.assertEqual(point.sign, sign)
            self.assertEqual(point.house, house)
            self.assertLessEqual(
                shortest_distance(point.longitude, expected_longitude(sign, degree, minute)),
                0.5,
            )

        self.assertLessEqual(
            shortest_distance(
                self.response.angles.asc.longitude,
                expected_longitude("Cancer", 23, 22),
            ),
            0.5,
        )
        self.assertLessEqual(
            shortest_distance(
                self.response.angles.mc.longitude,
                expected_longitude("Aries", 10, 2),
            ),
            0.5,
        )

    def test_whole_sign_houses_are_exact(self) -> None:
        expected_signs = [
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
            "Gemini",
        ]

        actual_signs = [house.sign for house in self.response.houses]
        self.assertEqual(actual_signs, expected_signs)
        self.assertEqual(self.response.houses[0].cusp_longitude, 90.0)
        self.assertEqual(self.response.houses[9].cusp_longitude, 0.0)

    def test_special_points_match_priority_targets(self) -> None:
        node = self.point_map["North Node"]
        lilith = self.point_map["Lilith"]
        fortune = self.point_map["Fortune"]
        vertex = self.point_map["Vertex"]

        self.assertEqual(node.sign, "Pisces")
        self.assertEqual(lilith.sign, "Virgo")
        self.assertLessEqual(shortest_distance(node.longitude, expected_longitude("Pisces", 9, 8)), 0.5)
        self.assertLessEqual(shortest_distance(lilith.longitude, expected_longitude("Virgo", 22, 53)), 0.5)
        self.assertLessEqual(shortest_distance(fortune.longitude, expected_longitude("Leo", 26, 29)), 0.5)
        self.assertLessEqual(shortest_distance(vertex.longitude, expected_longitude("Sagittarius", 7, 0)), 0.5)

    def test_key_aspects_include_expected_orb_and_direction(self) -> None:
        expectations = {
            ("Sun", "Conjunction", "Mercury"): False,
            ("Moon", "Conjunction", "Venus"): True,
            ("Moon", "Conjunction", "Pluto"): True,
            ("Mars", "Square", "Neptune"): True,
            ("MC", "Conjunction", "Mars"): False,
        }

        for key, applying in expectations.items():
            self.assertIn(key, self.aspect_map)
            self.assertEqual(self.aspect_map[key].applying, applying)


class NatalChartReferenceMatrixTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = NatalChartEngine()

    def test_reference_cases_match_expected_planets_angles_and_houses(self) -> None:
        for reference_case in REFERENCE_CASES:
            with self.subTest(reference_case=reference_case["id"]):
                birth_dt = datetime.fromisoformat(
                    f"{reference_case['birth_date']}T{reference_case['birth_time']}"
                ).replace(tzinfo=ZoneInfo(reference_case["timezone"]))
                chart = self.engine.calculate_chart(
                    birth_dt_local=birth_dt,
                    latitude=reference_case["latitude"],
                    longitude=reference_case["longitude"],
                )
                point_map = {point["name"]: point for point in chart["points"]}

                for point_name, (sign, degree, minute) in reference_case["expected_points"].items():
                    point = point_map[point_name]
                    self.assertEqual(point["sign"], sign)
                    self.assertLessEqual(
                        shortest_distance(point["longitude"], expected_longitude(sign, degree, minute)),
                        0.05,
                        point_name,
                    )

                for angle_name, (sign, degree, minute) in reference_case["expected_angles"].items():
                    angle = chart["angles"][angle_name]
                    self.assertEqual(angle["sign"], sign)
                    self.assertLessEqual(
                        shortest_distance(angle["longitude"], expected_longitude(sign, degree, minute)),
                        0.05,
                        angle_name,
                    )

                self.assertEqual(
                    [house["sign"] for house in chart["houses"]],
                    reference_case["expected_house_signs"],
                )


class NatalChartApiTestCase(unittest.TestCase):
    def test_natal_chart_endpoint_uses_ephemeris_files_in_worker_thread(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get(
            "/api/chart/natal",
            params={
                "birthDate": "1988-12-06",
                "birthTime": "19:59",
                "city": "Busan",
                "countryCode": "KR",
                "timezone": "Asia/Seoul",
            },
        )

        self.assertEqual(response.status_code, 200)
        point_names = {point["name"] for point in response.json()["points"]}
        self.assertIn("Chiron", point_names)
