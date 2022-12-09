from typing import Any, Generator, Tuple, Type, TypeVar

from json_codec.types import (
    ParseProcessResult,
    ParseProcessYield,
    TypeDecoder,
    ValidationError,
)

T = TypeVar("T")


class TupleTypeDecoder(TypeDecoder[Tuple[T, ...]]):
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any],
        ParseProcessResult[Any],
        ParseProcessResult[Tuple[T, ...]],
    ]:
        if not isinstance(value, list):
            return self._failure(ValidationError(f"Expected list, got {value}"))

        final_tuple: Tuple[T, ...] = ()

        # TODO: make sure tuple will match the types
        for i, (item_type, item) in enumerate(zip(types, value)):
            parsed_item = yield ParseProcessYield(item_type, item, json_path=f"[{i}]")

            if isinstance(parsed_item.result, Exception):
                raise parsed_item.result

            final_tuple += (parsed_item.result,)
        return self._success(final_tuple)
