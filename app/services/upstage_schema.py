"""Pydantic이 만든 JSON schema를 Upstage structured output 제약에 맞게 변환한다.

Upstage(`response_format.json_schema`)는 xAI보다 스키마 제약이 엄격하다.

- `$ref` / `$defs` 같은 로컬 정의 참조를 지원하지 않는다.
- 재귀 스키마를 지원하지 않는다.
- 모든 object는 `additionalProperties: false` 이고 전 프로퍼티가 `required` 여야 한다.
- object 중첩은 3단계까지만 허용한다.
- 타입은 string/number/boolean/integer/object/array 만 쓸 수 있다.

이 모듈은 순수 함수만 제공하며 다른 서비스에 의존하지 않는다. 기존 xai/deepseek/gemma
경로는 이 변환을 쓰지 않는다.
"""

from typing import Any, Optional

SUPPORTED_TYPES = frozenset({"string", "number", "boolean", "integer", "object", "array"})
MAX_OBJECT_DEPTH = 3

_FORMAT_HINTS = {
    "date": "YYYY-MM-DD 형식의 날짜 문자열",
    "date-time": "ISO 8601 형식의 날짜/시간 문자열",
    "time": "HH:MM 형식의 시각 문자열",
    "email": "이메일 주소 형식의 문자열",
    "uri": "URL 형식의 문자열",
}


class SchemaFlattenError(ValueError):
    """Upstage json_schema 제약으로 변환할 수 없는 스키마."""


def flatten_json_schema(
    schema: dict[str, Any],
    *,
    max_object_depth: int = MAX_OBJECT_DEPTH,
    keep_descriptions: bool = True,
    keep_enums: bool = True,
) -> dict[str, Any]:
    """`model_json_schema()` 결과를 Upstage가 받아들이는 형태로 평탄화한다.

    `keep_descriptions` / `keep_enums`는 Upstage가 해당 키워드를 거부할 때 끄기 위한
    탈출구다. 기본값은 둘 다 유지다.
    """
    defs: dict[str, Any] = {}
    defs.update(schema.get("$defs") or {})
    defs.update(schema.get("definitions") or {})
    return _convert(
        schema,
        defs=defs,
        depth=0,
        max_depth=max_object_depth,
        stack=(),
        keep_descriptions=keep_descriptions,
        keep_enums=keep_enums,
    )


def build_upstage_response_format(
    name: str,
    schema: dict[str, Any],
    **flatten_options: Any,
) -> dict[str, Any]:
    """Upstage chat completions 요청에 그대로 넣을 수 있는 `response_format`을 만든다."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": flatten_json_schema(schema, **flatten_options),
        },
    }


def _convert(
    node: dict[str, Any],
    *,
    defs: dict[str, Any],
    depth: int,
    max_depth: int,
    stack: tuple[str, ...],
    keep_descriptions: bool,
    keep_enums: bool,
) -> dict[str, Any]:
    node, stack = _deref(node, defs=defs, stack=stack)
    node = _collapse_unions(node)

    node_type = _resolve_type(node)
    if node_type not in SUPPORTED_TYPES:
        raise SchemaFlattenError(f"unsupported type: {node_type!r}")

    out: dict[str, Any] = {"type": node_type}

    if keep_descriptions:
        description = _description_for(node)
        if description:
            out["description"] = description

    if keep_enums and "enum" in node:
        out["enum"] = list(node["enum"])

    child_options = {
        "defs": defs,
        "max_depth": max_depth,
        "stack": stack,
        "keep_descriptions": keep_descriptions,
        "keep_enums": keep_enums,
    }

    if node_type == "object":
        level = depth + 1
        if level > max_depth:
            raise SchemaFlattenError(f"object nesting exceeds {max_depth} levels")
        properties = node.get("properties") or {}
        if not properties:
            # dict[str, X] 같은 free-form map은 strict 모드와 공존할 수 없다.
            raise SchemaFlattenError("object without properties is not supported")
        out["properties"] = {
            key: _convert(value, depth=level, **child_options) for key, value in properties.items()
        }
        out["required"] = list(properties.keys())
        out["additionalProperties"] = False
    elif node_type == "array":
        items = node.get("items")
        if not isinstance(items, dict):
            raise SchemaFlattenError("array items schema is required")
        # 배열은 object 중첩 레벨을 소비하지 않는다.
        out["items"] = _convert(items, depth=depth, **child_options)

    return out


def _deref(
    node: dict[str, Any],
    *,
    defs: dict[str, Any],
    stack: tuple[str, ...],
) -> tuple[dict[str, Any], tuple[str, ...]]:
    while "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or not (
            ref.startswith("#/$defs/") or ref.startswith("#/definitions/")
        ):
            raise SchemaFlattenError(f"unsupported $ref: {ref!r}")
        name = ref.rsplit("/", 1)[-1]
        if name in stack:
            raise SchemaFlattenError(f"recursive schema is not supported: {name}")
        target = defs.get(name)
        if target is None:
            raise SchemaFlattenError(f"missing definition: {ref}")
        stack = stack + (name,)
        sibling = {key: value for key, value in node.items() if key != "$ref"}
        node = {**target, **sibling}
    return node, stack


def _collapse_unions(node: dict[str, Any]) -> dict[str, Any]:
    for keyword in ("allOf", "anyOf", "oneOf"):
        if keyword not in node:
            continue
        branches = node[keyword]
        if not isinstance(branches, list):
            raise SchemaFlattenError(f"{keyword} must be a list")
        if keyword != "allOf":
            # Optional[X] 는 anyOf[X, null] 로 생성된다. null 브랜치만 걷어낸다.
            branches = [item for item in branches if item.get("type") != "null"]
        if len(branches) != 1:
            raise SchemaFlattenError(f"{keyword} with {len(branches)} branches is not supported")
        sibling = {key: value for key, value in node.items() if key != keyword}
        node = _collapse_unions({**branches[0], **sibling})
    return node


def _resolve_type(node: dict[str, Any]) -> Any:
    node_type = node.get("type")
    if isinstance(node_type, list):
        candidates = [item for item in node_type if item != "null"]
        if len(candidates) != 1:
            raise SchemaFlattenError(f"ambiguous type: {node_type!r}")
        return candidates[0]
    return node_type


def _description_for(node: dict[str, Any]) -> Optional[str]:
    """제거되는 제약 키워드를 사람이 읽는 설명으로 옮긴다."""
    parts: list[str] = []

    existing = node.get("description")
    if isinstance(existing, str) and existing.strip():
        parts.append(existing.strip())

    hint = _FORMAT_HINTS.get(node.get("format"))
    if hint:
        parts.append(hint)

    minimum = node.get("minimum", node.get("exclusiveMinimum"))
    maximum = node.get("maximum", node.get("exclusiveMaximum"))
    if minimum is not None and maximum is not None:
        parts.append(f"허용 범위 {minimum} ~ {maximum}")
    elif minimum is not None:
        parts.append(f"{minimum} 이상")
    elif maximum is not None:
        parts.append(f"{maximum} 이하")

    min_length = node.get("minLength")
    max_length = node.get("maxLength")
    if min_length is not None and max_length is not None:
        parts.append(f"길이 {min_length} ~ {max_length}자")
    elif min_length is not None:
        parts.append(f"최소 {min_length}자")
    elif max_length is not None:
        parts.append(f"최대 {max_length}자")

    pattern = node.get("pattern")
    if isinstance(pattern, str) and pattern:
        parts.append(f"정규식 {pattern} 을 만족")

    return " / ".join(parts) if parts else None
