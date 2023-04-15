from typing import Any, Generator, Type, TypeVar
from datetime import date, datetime

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class DateTypeDecoder(TypeDecoder[date]):
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[Any], ParseProcessResult[date]
    ]:
        if not isinstance(value, str):
            return self._failure(ValidationError(f"Expected string, got {value}"))

        try:
            return self._success(datetime.strptime(value, "%Y-%m-%d").date())
        except ValueError:
            return self._failure(
                ValidationError(
                    f"Expected date in format YYYY-MM-DD, but {value} is not a valid value"
                )
            )
        yield


def serialize_date(value: date) -> Any:
    return value.strftime("%Y-%m-%d")
