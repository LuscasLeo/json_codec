from typing import Any, Generator, List, Type, TypeVar, cast

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeArgsLengthMismatch,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")

from typing_extensions import Type


class ListTypeDecoder(TypeDecoder[List[T]]):
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[T], ParseProcessResult[List[T]]
    ]:
        if not isinstance(value, list):
            return self._failure(ValidationError(f"Expected list, got {value}"))

        if len(types) != 1:
            return self._failure(
                TypeArgsLengthMismatch(f"Expected 1 type argument, got {len(types)}")
            )

        list_type: Type[T] = cast(Type[T], types[0])

        parsed_list: List[T] = []

        for index, item in enumerate(value):
            parsed_item = yield ParseProcessYield(
                type_=list_type, value=item, json_path=f"[{index}]"
            )
            if isinstance(parsed_item.result, Exception):
                raise parsed_item.result
            parsed_list.append(parsed_item.result)

        return self._success(parsed_list)
