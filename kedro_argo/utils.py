import csv
from typing import Any, Dict, List


def split_string(ctx, param, value):  # pylint: disable=unused-argument
    """Split string by comma."""
    return [item.strip() for item in value.split(",") if item.strip()]


def _try_convert_to_numeric(value):
    try:
        value = float(value)
    except ValueError:
        return value
    return int(value) if value.is_integer() else value


def _split_params(ctx, param, value):
    if isinstance(value, dict):  # pragma: no cover
        return value
    result = {}
    for item in split_string(ctx, param, value):
        item = item.split(":", 1)
        if len(item) != 2:
            ctx.fail(
                f"Invalid format of `{param.name}` option: "
                f"Item `{item[0]}` must contain "
                f"a key and a value separated by `:`."
            )
        key = item[0].strip()
        if not key:
            ctx.fail(
                f"Invalid format of `{param.name}` option: Parameter key "
                f"cannot be an empty string."
            )
        value = item[1].strip()
        [path] = list(csv.reader([key], delimiter="."))
        result = _update_value_nested_dict(result, _try_convert_to_numeric(value), path)
    return result


def _update_value_nested_dict(
    nested_dict: Dict[str, Any], value: Any, walking_path: List[str]
) -> Dict:
    """Update nested dict with value using walking_path as a parse tree to walk
    down the nested dict.

    Example:
    ::
        >>> nested_dict = {"foo": {"hello": "world", "bar": 1}}
        >>> _update_value_nested_dict(nested_dict, value=2, walking_path=["foo", "bar"])
        >>> print(nested_dict)
        >>> {'foo': {'hello': 'world', 'bar': 2}}

    Args:
        nested_dict: dict to be updated
        value: value to update the nested_dict with
        walking_path: list of nested keys to use to walk down the nested_dict

    Returns:
        nested_dict updated with value at path `walking_path`
    """
    key = walking_path.pop(0)
    if not walking_path:
        nested_dict[key] = value
        return nested_dict
    nested_dict[key] = _update_value_nested_dict(
        nested_dict.get(key, {}), value, walking_path
    )
    return nested_dict


def _update_nested_dict(old_dict: Dict[Any, Any], new_dict: Dict[Any, Any]) -> None:
    """Update a nested dict with values of new_dict.

    Args:
        old_dict: dict to be updated
        new_dict: dict to use for updating old_dict

    """
    for key, value in new_dict.items():
        if key not in old_dict:
            old_dict[key] = value
        else:
            if isinstance(old_dict[key], dict) and isinstance(value, dict):
                _update_nested_dict(old_dict[key], value)
            else:
                old_dict[key] = value
