from typing import Any
import kopf

def check_required_field(field, value):
    if not value:
        raise kopf.PermanentError(f"{field} is required, got: {value!r}.")

def check_required_fields(spec, fields: list[str]) -> None:
    parsed_fields: list[list[str]] = [field.split('.') for field in fields]
    root_fields: list[str] = [field[0] for field in parsed_fields]


    # Check root fields
    for r_field in root_fields:
        r_value = spec.get(r_field)
        check_required_field(r_field, r_value)

        # Check nested fields
        nested_fields = [field[1:] for field in parsed_fields if field[0] == r_field and len(field) > 1]
        if nested_fields:
            nested_fields = ['.'.join(field) for field in nested_fields]
            check_required_fields(r_value, nested_fields)

def to_camel(snake_str: str) -> str:
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

def keys_to_camel(data: dict[str, Any] | list[Any] | Any) -> dict[str, Any] | list[Any] | Any:
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = to_camel(key)
            new_data[new_key] = keys_to_camel(value)
        return new_data
    elif isinstance(data, list):
        return [keys_to_camel(x) for x in data]
    else:
        return data

def ommit_none(data: dict[str, Any] | list[Any] | Any) -> dict[str, Any] | list[Any] | Any:
    if isinstance(data, dict):
        return {k: ommit_none(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [ommit_none(x) for x in data]
    else:
        return data

def ommit_empty(data: dict[str, Any] | list[Any] | Any) -> dict[str, Any] | list[Any] | Any:
    if isinstance(data, dict):
        return {k: ommit_empty(v) for k, v in data.items() if v != ""}
    elif isinstance(data, list):
        return [ommit_empty(x) for x in data]
    else:
        return data
