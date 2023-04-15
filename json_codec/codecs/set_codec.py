from typing import Any, Generator, Set, Type, TypeVar

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeArgsLengthMismatch,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class SetTypeDecoder(TypeDecoder[Set[T]]):
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any],
        ParseProcessResult[Any],
        ParseProcessResult[Set[T]],
    ]:
        if not isinstance(value, list):
            return self._failure(ValidationError(f"Expected list, got {value}"))

        if len(types) != 1:
            return self._failure(
                TypeArgsLengthMismatch(f"Expected 1 type argument, got {len(types)}")
            )

        item_type = types[0]
        initial_set = set()

        for index, item in enumerate(value):
            parsed_item = yield ParseProcessYield(
                item_type, item, json_path=f"[{index}]"
            )
            if isinstance(parsed_item.result, Exception):
                raise parsed_item.result

            initial_set.add(parsed_item.result)

        return self._success(initial_set)
