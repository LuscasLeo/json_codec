import base64
from dataclasses import MISSING, asdict, dataclass, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

from json_codec.codecs.date_codec import (
    DateTypeDecoder,
    serialize_date,
)
from json_codec.codecs.datetime_codec import (
    DateTimeTypeDecoder,
    serialize_datetime,
)
from json_codec.codecs.dict_codec import DictTypeDecoder
from json_codec.codecs.list_codec import (
    ListTypeDecoder as ListTypeParser,
)
from json_codec.codecs.primitive_codec import PrimitiveTypeDecoder
from json_codec.codecs.set_codec import (
    SetTypeDecoder as SetTypeParser,
)
from json_codec.codecs.time_codec import (
    TimeTypeDecoder as TimeTypeParser,
)
from json_codec.codecs.time_codec import serialize_time
from json_codec.codecs.tuple_codec import (
    TupleTypeDecoder as TupleTypeParser,
)
from json_codec.codecs.union_codec import (
    UnionTypeDecoder as UnionTypeParser,
)
from json_codec.types import (
    AssumeDataclass,
    AssumeGeneric,
    AssumeNewType,
    ParseProcessResult,
    TypeDecoder,
    ValidationError,
)
from json_codec.utils import is_generic

T = TypeVar("T")

typers_parsers: Dict[Any, TypeDecoder[Any]] = {
    Decimal: PrimitiveTypeDecoder(Decimal, "Decimal"),
    str: PrimitiveTypeDecoder(str, "string"),
    int: PrimitiveTypeDecoder(int, "int"),
    float: PrimitiveTypeDecoder(float, "float"),
    bool: PrimitiveTypeDecoder(bool, "bool"),
    dict: DictTypeDecoder(),
    list: ListTypeParser(),
    tuple: TupleTypeParser(),
    set: SetTypeParser(),
    UUID: PrimitiveTypeDecoder(UUID, "UUID"),
    Union: UnionTypeParser(),
    Any: PrimitiveTypeDecoder(lambda x: x, "Any"),
    date: DateTypeDecoder(),
    datetime: DateTimeTypeDecoder(),
    time: TimeTypeParser(),
    type(None): PrimitiveTypeDecoder(lambda x: None, "null"),
    bytes: PrimitiveTypeDecoder(base64.b64decode, "bytes"),
}


@dataclass
class LocatedValidationError:
    message: str
    json_path: str


class LocatedValidationErrorCollection(Exception):
    def __init__(self, errors: List[LocatedValidationError]) -> None:
        super().__init__("Located validation errors: %s" % errors)
        self.errors = errors

    def __str__(self) -> str:
        return "\n".join(["{}: {}".format(e.json_path, str(e)) for e in self.errors])


def __get_recursive_mapped_type(cls_type: Type[Any]) -> Type[Any]:
    if not hasattr(cls_type, "__bases__") or len(cls_type.__bases__) == 0:
        return cls_type

    while cls_type not in typers_parsers:
        cls_type = cls_type.__bases__[0]
        if cls_type not in typers_parsers:
            return __get_recursive_mapped_type(cls_type)
    return cls_type


def is_new_type(type_: Type[Any]) -> bool:
    return hasattr(type_, "__supertype__")


def get_new_type_supertype(type_: Type[Any]) -> Type[Any]:
    return cast(AssumeNewType, type_).__supertype__


def is_typing_unmappable(type_: Type[Any]) -> bool:
    return type_ is Any or type_ is type(None)


def __parse_value(
    value: Any,
    type_: Type[T],
    json_path: str = "$",
    located_errors: List[LocatedValidationError] = [],
    skip_raise: bool = False,
) -> ParseProcessResult[T]:
    real_type = type_
    target_type = type_
    type_args: Tuple[Type[Any], ...] = ()
    if is_typing_unmappable(type_):
        ...
    elif is_generic(type_):
        real_type = cast(AssumeGeneric, type_).__origin__
        target_type = real_type
        type_args = cast(AssumeGeneric, type_).__args__
    elif is_new_type(type_):
        target_type = get_new_type_supertype(type_)
    elif not is_dataclass(type_) and not issubclass(real_type, Enum):
        target_type = __get_recursive_mapped_type(type_)

    if target_type in typers_parsers:
        parser = typers_parsers[target_type]
        parser_generator = parser.parse(value, *type_args)
        try:
            parsed_yield = parser_generator.send(cast(Any, None))
            while True:
                parsed_value = __parse_value(
                    parsed_yield.value,
                    parsed_yield.type_,
                    "{}{}".format(json_path, parsed_yield.json_path),
                    located_errors,
                    parsed_yield.skip_raise,
                )
                parsed_yield = parser_generator.send(parsed_value)
        except StopIteration as e:
            final = e.value
            if not isinstance(final, ParseProcessResult):
                raise ValueError(f"Parser {parser} did not return a ParseProcessResult")
            if isinstance(final.result, Exception) and not skip_raise:
                located_errors.append(
                    LocatedValidationError(
                        message=str(final.result),
                        json_path=json_path,
                    )
                )

            if target_type != real_type:
                if not isinstance(final.result, Exception):
                    final = ParseProcessResult(
                        result=cast(Type[Any], real_type)(final.result),
                    )
                else:
                    final = ParseProcessResult(
                        result=None,
                    )

            return cast(ParseProcessResult[T], final)

    elif is_dataclass(real_type):
        try:
            return ParseProcessResult(
                __parse_dataclass(
                    value,
                    real_type,
                    json_path,
                    located_errors,
                )
            )
        except AssertionError as e:
            error = ValidationError(
                str(e),
            )
            if not skip_raise:
                located_errors.append(
                    LocatedValidationError(
                        message=str(error),
                        json_path=json_path,
                    )
                )
            return ParseProcessResult(error)
    elif issubclass(real_type, Enum):
        try:
            value = real_type(value)
            return ParseProcessResult(value)
        except ValueError:
            error = ValidationError(
                "Invalid enum value for {}: {} | valid types: {}".format(
                    real_type,
                    value,
                    ", ".join(k for k, v in real_type.__members__.items()),
                )
            )
            if not skip_raise:
                located_errors.append(
                    LocatedValidationError(
                        message=str(error),
                        json_path=json_path,
                    )
                )
            return ParseProcessResult(error)

    else:
        raise ValueError(f"Unsupported type: {type_}")


def __parse_dataclass(
    value: Any,
    type_: Type[T],
    json_path: str = "$",
    located_errors: List[LocatedValidationError] = [],
) -> T:
    assert isinstance(value, dict), "Value must be a dict"

    assert is_dataclass(type_), "Type must be a dataclass"

    fields = cast(AssumeDataclass, type_).__dataclass_fields__

    kwargs: Dict[str, Any] = {}

    for field_name, field in fields.items():
        field_json_path = "{}.{}".format(json_path, field_name)

        if field_name not in value:
            if field.default is not None and field.default is not MISSING:
                kwargs[field_name] = field.default
            elif field.default_factory is not None and field.default_factory is not MISSING:  # type: ignore
                kwargs[field_name] = field.default_factory()  # type: ignore
            else:
                kwargs[field_name] = None
                located_errors.append(
                    LocatedValidationError(
                        message="Missing required field: {}".format(field_name),
                        json_path=json_path,
                    )
                )
            continue

        parsed_value = __parse_value(
            value[field_name],
            field.type,
            field_json_path,
            located_errors,
        )

        kwargs[field_name] = parsed_value.result

    return cast(Callable[..., T], type_)(**kwargs)


def decode(value: Any, type_: Type[T]) -> T:
    errors: List[LocatedValidationError] = []
    parsed_value = __parse_value(value, type_, located_errors=errors)
    if len(errors):
        raise LocatedValidationErrorCollection(errors)

    if isinstance(parsed_value.result, Exception):
        raise parsed_value.result

    return parsed_value.result


def optional(T: Type[T]) -> Type[T]:
    return Optional[T]  # type: ignore


def __encode(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return serialize_datetime(value)
    if isinstance(value, date):
        return serialize_date(value)
    if isinstance(value, time):
        return serialize_time(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (Decimal, UUID, str)):
        return str(value)
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [__encode(v) for v in value]
    if isinstance(value, dict):
        return {__encode(k): __encode(v) for k, v in value.items()}
    if is_dataclass(value):
        return __encode(asdict(value))
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("utf-8")
    if value is None:
        return None
    raise ValueError(f"Unsupported type: {type(value)}")


def encode(value: Any) -> Any:
    return __encode(value)
