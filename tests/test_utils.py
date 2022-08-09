from typing import Dict

import pytest

from kedro_argo.utils import _update_nested_dict


@pytest.mark.parametrize(
    "old_dict, new_dict, expected",
    [
        (
            {
                "a": 1,
                "b": 2,
                "c": {
                    "d": 3,
                },
            },
            {"c": {"d": 5, "e": 4}},
            {
                "a": 1,
                "b": 2,
                "c": {"d": 5, "e": 4},
            },
        ),
        ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
        ({"a": 1, "b": 2}, {"b": 3}, {"a": 1, "b": 3}),
        (
            {"a": {"a.a": 1, "a.b": 2, "a.c": {"a.c.a": 3}}},
            {"a": {"a.c": {"a.c.b": 4}}},
            {"a": {"a.a": 1, "a.b": 2, "a.c": {"a.c.a": 3, "a.c.b": 4}}},
        ),
    ],
)
def test_update_nested_dict(old_dict: Dict, new_dict: Dict, expected: Dict):
    _update_nested_dict(old_dict, new_dict)  # _update_nested_dict change dict in place
    assert old_dict == expected
