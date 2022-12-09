from abc import ABC, abstractmethod
from dataclasses import Field, dataclass
from typing import (
    Any,
    Dict,
    Generator,
    Generic,
    List,
    Tuple,
    TypeVar,
    Union,
)

from typing_extensions import Protocol, Type


class AssumeDataclass(Protocol):
    # as already noted in comments, checking for this attribute is currently
    # the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: "Dict[str, Field[Any]]"


class AssumeGeneric(Protocol):
    __origin__: Type[Any]
    __args__: Tuple[Type[Any], ...]
    _name: str


class AssumeNewType(Protocol):
    __supertype__: Type[Any]


T = TypeVar("T")


class ValidationErrorBase(Exception):
    pass


class ValidationError(ValidationErrorBase):
    pass


class TypeValuesMismatch(ValidationError):
    pass


class TypeNotSupported(ValidationError):
    pass


class TypeArgsLengthMismatch(ValidationError):
    pass


class ValidationErrorCollection(ValidationErrorBase):
    def __init__(self, errors: List[ValidationErrorBase]) -> None:
        self.errors = errors

    def __str__(self) -> str:
        return ", ".join([str(error) for error in self.errors])


def flat_error_collection(
    errors: List[ValidationErrorBase],
) -> List[ValidationErrorBase]:
    flat_errors: List[ValidationErrorBase] = []
    for error in errors:
        if isinstance(error, ValidationErrorCollection):
            flat_errors.extend(flat_error_collection(error.errors))
        else:
            flat_errors.append(error)
    return flat_errors


@dataclass
class ParseProcessResult(Generic[T]):
    result: Union[ValidationErrorBase, T]


@dataclass
class ParseProcessYield(Generic[T]):
    value: T
    type_: Type[T]
    json_path: str
    skip_raise: bool = False


class TypeDecoder(Generic[T], ABC):
    @abstractmethod
    def parse(
        self, value: Any, *types: Type[Any]
    ) -> Generator[
        ParseProcessYield[Any], ParseProcessResult[Any], ParseProcessResult[T]
    ]:
        raise NotImplementedError()

    def _success(self, value: T) -> ParseProcessResult[T]:
        return ParseProcessResult[T](result=value)

    def _failure(self, error: ValidationErrorBase) -> ParseProcessResult[T]:
        return ParseProcessResult[T](result=error)
