"""Inline properties of unnamed ``allOf`` members must be named per enclosing schema, never shared."""

from __future__ import annotations

from typing import Any

import pytest

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.core.loader import load_ir_from_spec


def _variant(status_values: list[str], extra_properties: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "allOf": [
            {"$ref": "#/components/schemas/Base"},
            {
                "type": "object",
                "required": ["status"],
                "properties": {
                    "status": {"type": "string", "enum": status_values},
                    **(extra_properties or {}),
                },
            },
        ]
    }


def _spec(schemas: dict[str, Any]) -> dict[str, Any]:
    base = {"type": "object", "properties": {"id": {"type": "string"}}}
    return {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {},
        "components": {"schemas": {"Base": base, **schemas}},
    }


def _status_schema(ir: IRSpec, owner: str) -> IRSchema:
    """The named schema that ``owner.status`` resolves to."""
    prop = ir.schemas[owner].properties["status"]
    name = prop.name or prop.type
    assert name is not None and name in ir.schemas, f"{owner}.status is not a registered schema: {prop}"
    return ir.schemas[name]


def test_load_ir__allof_members_with_same_property_name__each_keeps_its_own_enum_values() -> None:
    """
    Scenario:
        Three schemas each extend a base with an inline ``allOf`` member declaring a ``status`` enum with
        different values (the shape of a discriminated result union).

    Expected Outcome:
        Every schema's ``status`` resolves to a distinct enum holding exactly its own values; none is
        replaced by the first one parsed.
    """
    # Arrange
    spec = _spec(
        {
            "Covered": _variant(["covered"]),
            "NotCovered": _variant(["not-covered"]),
            "Unknown": _variant(["waived", "no-plan"]),
        }
    )

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    values = {owner: _status_schema(ir, owner).enum for owner in ("Covered", "NotCovered", "Unknown")}
    assert values == {"Covered": ["covered"], "NotCovered": ["not-covered"], "Unknown": ["waived", "no-plan"]}
    names = {_status_schema(ir, owner).name for owner in values}
    assert len(names) == 3


def test_load_ir__allof_member_enum__named_after_enclosing_schema() -> None:
    """
    Scenario:
        A schema's unnamed ``allOf`` member declares an inline ``status`` enum.

    Expected Outcome:
        The enum is registered under the enclosing schema's name plus the property name, matching how
        inline enums of directly declared properties are named.
    """
    # Arrange
    spec = _spec({"Covered": _variant(["covered"])})

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    assert "CoveredStatus" in ir.schemas
    assert ir.schemas["CoveredStatus"].enum == ["covered"]


def test_load_ir__allof_members_with_same_inline_object_property__each_keeps_its_own_shape() -> None:
    """
    Scenario:
        Two schemas' ``allOf`` members each declare an inline object ``details`` property with different
        fields.

    Expected Outcome:
        Each schema's ``details`` is promoted under its own name and keeps its own fields.
    """
    # Arrange
    details_a = {"type": "object", "description": "A", "properties": {"a": {"type": "string"}}}
    details_b = {"type": "object", "description": "B", "properties": {"b": {"type": "integer"}}}
    spec = _spec(
        {
            "One": _variant(["x"], {"details": details_a}),
            "Two": _variant(["y"], {"details": details_b}),
        }
    )

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    promoted = {owner: ir.schemas[ir.schemas[owner].properties["details"].type or ""] for owner in ("One", "Two")}
    assert set(promoted["One"].properties) == {"a"}
    assert set(promoted["Two"].properties) == {"b"}


@pytest.mark.parametrize("owner", ["Covered", "Other"])
def test_load_ir__directly_declared_enum__naming_unchanged(owner: str) -> None:
    """
    Scenario:
        An inline enum is declared directly on a named schema's properties (no ``allOf``).

    Expected Outcome:
        It is still named ``<Schema><Property>``; scoping by the enclosing schema changes nothing here.
    """
    # Arrange
    spec = _spec({owner: {"type": "object", "properties": {"status": {"type": "string", "enum": ["a", "b"]}}}})

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    assert ir.schemas[f"{owner}Status"].enum == ["a", "b"]
