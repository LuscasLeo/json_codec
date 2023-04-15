from typing import Any, Dict, Generator, Type, TypeVar

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeArgsLengthMismatch,
    TypeDecoder,
    ValidationError,
)

K = TypeVar("K")
V = TypeVar("V")


class DictKeyError(Exception):
    def __init__(self, key: str, error: ValidationError) -> None:
        super().__init__(f"Error in key {key}: {error}")
        self.key = key
        self.error = error


class DictValueError(Exception):
    def __init__(self, key: str, value: Any, error: ValidationError) -> None:
        super().__init__(f"Error in value {value} for key {key}: {error}")
        self.key = key
        self.value = value
        self.error = error


class DictTypeDecoder(TypeDecoder[Dict[K, V]]):
    def parse(
        self, dict_item: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[Any], ParseProcessResult[Dict[K, V]]
    ]:
        if not isinstance(dict_item, dict):
            return self._failure(
                ValidationError(f"Expected dict, got {type(dict_item)}")
            )

        if len(types) != 2:
            return self._failure(
                TypeArgsLengthMismatch(f"Expected 2 type arguments, got {len(types)}")
            )

        key_type = types[0]
        value_type = types[1]
        initial_dict: Dict[K, V] = {}

        for key, value in dict_item.items():
            key_json_path = f"['{key}'] (key)"

            parsed_key = yield ParseProcessYield(key, key_type, key_json_path)

            value_json_path = f"['{key}'] (value)"
            parsed_value = yield ParseProcessYield(value, value_type, value_json_path)

            if not isinstance(parsed_key.result, Exception) and not isinstance(
                parsed_value.result, Exception
            ):
                initial_dict[parsed_key.result] = parsed_value.result
            # else:
            #     if isinstance(parsed_key.result, ValidationErrorBase):
            #         errors.append(parsed_key.result)
            #     if isinstance(parsed_value.result, ValidationErrorBase):
            #         errors.append(parsed_value.result)

        return self._success(initial_dict)
