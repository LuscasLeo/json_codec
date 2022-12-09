from typing import Any, Callable, Generator, Tuple, Type, TypeVar

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class PrimitiveTypeDecoder(TypeDecoder[T]):
    def __init__(self, type_: Callable[..., T]) -> None:
        self.type_ = type_

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
                    f"Expected type {self.type_}, but {value} is not a valid value"
                )
            )
        yield


def serialize_primitive(value: Any) -> Any:
    return str(value)
