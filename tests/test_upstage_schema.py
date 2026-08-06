import unittest
from typing import Optional

from pydantic import BaseModel

from app.schemas.ai_retention import (
    ActionCalendarLLMResponse,
    CoachLLMResponse,
    DailyBriefLLMResponse,
)
from app.schemas.horoscope import MonthlyHoroscopeLLMResponse
from app.services.upstage_schema import (
    SchemaFlattenError,
    build_upstage_response_format,
    flatten_json_schema,
)

PRODUCTION_MODELS = (
    ActionCalendarLLMResponse,
    DailyBriefLLMResponse,
    CoachLLMResponse,
    MonthlyHoroscopeLLMResponse,
)

UNSUPPORTED_KEYWORDS = (
    "$ref",
    "$defs",
    "definitions",
    "title",
    "format",
    "default",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "pattern",
    "anyOf",
    "oneOf",
    "allOf",
)


def walk(node: dict) -> list[dict]:
    """스키마의 모든 노드를 평평한 리스트로 모은다."""
    nodes = [node]
    for child in (node.get("properties") or {}).values():
        nodes.extend(walk(child))
    items = node.get("items")
    if isinstance(items, dict):
        nodes.extend(walk(items))
    return nodes


def object_depth(node: dict) -> int:
    children = list((node.get("properties") or {}).values())
    items = node.get("items")
    if isinstance(items, dict):
        children.append(items)
    deepest = max((object_depth(child) for child in children), default=0)
    return deepest + 1 if node.get("type") == "object" else deepest


class FlattenJsonSchemaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.calendar = flatten_json_schema(ActionCalendarLLMResponse.model_json_schema())
        self.day = self.calendar["properties"]["days"]["items"]

    def test_removes_all_refs_and_defs(self) -> None:
        for node in walk(self.calendar):
            for keyword in ("$ref", "$defs", "definitions"):
                self.assertNotIn(keyword, node)

    def test_inlines_referenced_definition(self) -> None:
        self.assertEqual(self.day["type"], "object")
        self.assertEqual(self.day["properties"]["title"]["type"], "string")

    def test_every_object_requires_all_properties(self) -> None:
        for node in walk(self.calendar):
            if node.get("type") == "object":
                self.assertEqual(node["required"], list(node["properties"].keys()))

    def test_every_object_disallows_additional_properties(self) -> None:
        for node in walk(self.calendar):
            if node.get("type") == "object":
                self.assertIs(node["additionalProperties"], False)

    def test_strips_unsupported_keywords(self) -> None:
        for node in walk(self.calendar):
            for keyword in UNSUPPORTED_KEYWORDS:
                self.assertNotIn(keyword, node)

    def test_enum_values_are_preserved(self) -> None:
        self.assertEqual(
            self.day["properties"]["tone"]["enum"],
            ["supportive", "neutral", "challenging"],
        )
        self.assertEqual(
            self.day["properties"]["categories"]["items"]["enum"],
            ["career", "money", "love", "risk"],
        )

    def test_date_format_moves_into_description(self) -> None:
        date_node = self.day["properties"]["date"]
        self.assertEqual(date_node["type"], "string")
        self.assertIn("YYYY-MM-DD", date_node["description"])

    def test_score_range_moves_into_description(self) -> None:
        score_node = self.day["properties"]["score"]
        self.assertEqual(score_node["type"], "integer")
        self.assertIn("1", score_node["description"])
        self.assertIn("10", score_node["description"])

    def test_all_production_schemas_flatten_within_depth_limit(self) -> None:
        for model in PRODUCTION_MODELS:
            with self.subTest(model=model.__name__):
                flattened = flatten_json_schema(model.model_json_schema())
                self.assertLessEqual(object_depth(flattened), 3)

    def test_keep_enums_false_drops_enum(self) -> None:
        flattened = flatten_json_schema(
            ActionCalendarLLMResponse.model_json_schema(), keep_enums=False
        )
        tone = flattened["properties"]["days"]["items"]["properties"]["tone"]
        self.assertNotIn("enum", tone)
        self.assertEqual(tone["type"], "string")

    def test_keep_descriptions_false_drops_description(self) -> None:
        flattened = flatten_json_schema(
            ActionCalendarLLMResponse.model_json_schema(), keep_descriptions=False
        )
        for node in walk(flattened):
            self.assertNotIn("description", node)


class FlattenJsonSchemaEdgeCaseTestCase(unittest.TestCase):
    def test_optional_field_collapses_anyof_null(self) -> None:
        class OptionalModel(BaseModel):
            note: Optional[str] = None

        flattened = flatten_json_schema(OptionalModel.model_json_schema())

        self.assertEqual(flattened["properties"]["note"]["type"], "string")
        self.assertEqual(flattened["required"], ["note"])

    def test_raises_on_recursive_schema(self) -> None:
        class Node(BaseModel):
            name: str
            child: Optional["Node"] = None

        Node.model_rebuild()

        with self.assertRaises(SchemaFlattenError):
            flatten_json_schema(Node.model_json_schema())

    def test_raises_when_object_depth_exceeds_limit(self) -> None:
        class Level4(BaseModel):
            value: str

        class Level3(BaseModel):
            nested: Level4

        class Level2(BaseModel):
            nested: Level3

        class Level1(BaseModel):
            nested: Level2

        with self.assertRaises(SchemaFlattenError):
            flatten_json_schema(Level1.model_json_schema())

    def test_allows_depth_exactly_at_limit(self) -> None:
        class Level3(BaseModel):
            value: str

        class Level2(BaseModel):
            nested: Level3

        class Level1(BaseModel):
            nested: Level2

        flattened = flatten_json_schema(Level1.model_json_schema())

        self.assertEqual(object_depth(flattened), 3)

    def test_raises_on_free_form_dict(self) -> None:
        class MapModel(BaseModel):
            scores: dict[str, float]

        with self.assertRaises(SchemaFlattenError):
            flatten_json_schema(MapModel.model_json_schema())

    def test_raises_on_missing_definition(self) -> None:
        with self.assertRaises(SchemaFlattenError):
            flatten_json_schema(
                {
                    "type": "object",
                    "properties": {"item": {"$ref": "#/$defs/Missing"}},
                }
            )

    def test_raises_on_external_ref(self) -> None:
        with self.assertRaises(SchemaFlattenError):
            flatten_json_schema(
                {
                    "type": "object",
                    "properties": {"item": {"$ref": "https://example.com/schema.json"}},
                }
            )

    def test_raises_on_union_of_two_types(self) -> None:
        with self.assertRaises(SchemaFlattenError):
            flatten_json_schema(
                {
                    "type": "object",
                    "properties": {
                        "value": {"anyOf": [{"type": "string"}, {"type": "integer"}]}
                    },
                }
            )

    def test_raises_on_array_without_items(self) -> None:
        with self.assertRaises(SchemaFlattenError):
            flatten_json_schema({"type": "object", "properties": {"items": {"type": "array"}}})


class BuildUpstageResponseFormatTestCase(unittest.TestCase):
    def test_response_format_shape(self) -> None:
        response_format = build_upstage_response_format(
            "action_calendar", ActionCalendarLLMResponse.model_json_schema()
        )

        self.assertEqual(response_format["type"], "json_schema")
        self.assertEqual(response_format["json_schema"]["name"], "action_calendar")
        self.assertIs(response_format["json_schema"]["strict"], True)
        self.assertEqual(response_format["json_schema"]["schema"]["type"], "object")

    def test_forwards_flatten_options(self) -> None:
        response_format = build_upstage_response_format(
            "action_calendar",
            ActionCalendarLLMResponse.model_json_schema(),
            keep_enums=False,
        )
        day = response_format["json_schema"]["schema"]["properties"]["days"]["items"]

        self.assertNotIn("enum", day["properties"]["tone"])


if __name__ == "__main__":
    unittest.main()
