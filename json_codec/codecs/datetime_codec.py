from typing import Any, Generator, Type, TypeVar
from datetime import datetime, timezone

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class DateTimeTypeDecoder(TypeDecoder[datetime]):
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[Any], ParseProcessResult[datetime]
    ]:
        if not isinstance(value, str):
            return self._failure(ValidationError(f"Expected string, got {value}"))

        try:
            # parse with iso format: 2020-01-01T00:00:00+00:00
            return self._success(datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z"))
        except ValueError:
            return self._failure(
                ValidationError(
                    f"Expected datetime in iso format, got {value} (expected format: 2020-01-01T00:00:00+00:00)"
                )
            )
        yield


def serialize_datetime(value: datetime) -> Any:
    return value.astimezone(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
