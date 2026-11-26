"""Bounded, duplicate-key-rejecting JSON for scientific source inputs.

Reject ambiguous object keys and non-finite numbers instead of silently
accepting the last key or non-standard Python JSON extensions. Never executes
user content. Shared by the topology editor, file imports, and catalogs.
"""
from __future__ import annotations

import json
from typing import Any


class ScientificJSONError(ValueError):
    """Input is ambiguous, invalid, or exceeds the source-size contract."""


def loads_scientific_json(text: str, *, max_bytes: int = 200_000) -> Any:
    if not isinstance(text, str):
        raise ScientificJSONError('Scientific JSON input must be text.')
    if len(text.encode('utf-8')) > max_bytes:
        raise ScientificJSONError(f'Scientific JSON exceeds {max_bytes} bytes.')

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ScientificJSONError(f'Duplicate JSON field {key!r}; no value was accepted.')
            result[key] = value
        return result

    def reject_constant(value):
        raise ScientificJSONError(f'Non-finite numeric value {value!r} is not permitted.')

    try:
        return json.loads(text, object_pairs_hook=unique_pairs,
                          parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeError, RecursionError, ValueError) as exc:
        raise ScientificJSONError(f'Invalid scientific JSON: {exc}') from exc
