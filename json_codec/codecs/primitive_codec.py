from typing import Any, Callable, Generator, Type, TypeVar

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class PrimitiveTypeDecoder(TypeDecoder[T]):
    def __init__(self, type_: Callable[..., T], type_name: str) -> None:
        self.type_ = type_
        self.type_name = type_name

    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[Any], ParseProcessResult[T]
    ]:
        try:
            return self._success(self.type_(value))
        except ValueError:
            return self._failure(
                ValidationError(
                    f"Expected type {self.type_name}, but '{value}' is not a valid value"
                )
            )
        yield


def serialize_primitive(value: Any) -> Any:
    return str(value)
