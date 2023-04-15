from typing import Any, Generator, Type, TypeVar

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class UnionTypeDecoder(TypeDecoder[Any]):
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[Any], ParseProcessResult[Any]
    ]:
        if type(value) in types:
            result = yield ParseProcessYield(
                type_=type(value),
                value=value,
                json_path="",
            )
            return result
        for type_ in types:
            parse_result = yield ParseProcessYield(
                type_=type_, value=value, json_path="", skip_raise=True
            )
            if not isinstance(parse_result.result, Exception):
                return parse_result

        return self._failure(
            ValidationError(f"Value {value} does not match any of the union types")
        )
