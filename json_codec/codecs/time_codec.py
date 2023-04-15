from typing import Any, Generator, Type, TypeVar
from datetime import datetime, time

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class TimeTypeDecoder(TypeDecoder[time]):
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[Any], ParseProcessResult[time]
    ]:
        if not isinstance(value, str):
            return self._failure(ValidationError(f"Expected string, got {value}"))

        try:
            return self._success(datetime.strptime(value, "%H:%M:%S").time())
        except ValueError:
            return self._failure(
                ValidationError(
                    f"Expected date in format YYYY-MM-DD, but {value} is not a valid value"
                )
            )
        yield


def serialize_time(value: time) -> Any:
    return value.strftime("%H:%M:%S")
