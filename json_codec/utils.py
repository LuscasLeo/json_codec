from dataclasses import is_dataclass
from typing import Any, Type, cast

from json_codec.types import AssumeGeneric


def get_class_or_type_name(type_: Type[Any]) -> str:
    if is_generic(type_):
        return cast(AssumeGeneric, type_).__repr__()

    if is_dataclass(type_):
        return type_.__name__

    return type_.__qualname__


def is_generic(type_: Type[Any]) -> bool:
    return (
        hasattr(type_, "__origin__")
        and cast(AssumeGeneric, type_).__origin__ is not None
    )
