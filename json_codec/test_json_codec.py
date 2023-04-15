import base64
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, NewType, Optional, Union

import pytest

from json_codec.json_codec import (
    LocatedValidationErrorCollection,
    decode,
    encode,
    optional,
)
from json_codec.utils import get_class_or_type_name


class TestJsonDeserializerCodec:
    def test_decode_primitives(self) -> None:
        assert decode(json.loads("true"), bool) is True
        assert decode(json.loads("false"), bool) is False
        assert decode(json.loads("null"), optional(bool)) is None
        assert decode(json.loads("1"), int) == 1
        assert decode(json.loads("1"), Decimal) == Decimal("1")
        assert decode(json.loads('"1.1"'), Decimal) == Decimal("1.1")
        assert decode(json.loads('"1.1"'), float) == 1.1
        assert decode(json.loads('"1.1"'), str) == "1.1"

        assert decode(json.loads("[1,1]"), List[int]) == [1, 1]

    def test_frozen_dataclass(self) -> None:
        @dataclass(frozen=True)
        class User:
            name: str
            age: int

        assert decode({"name": "John", "age": 30}, User) == User(name="John", age=30)

    def test_basic_dataclass(self) -> None:
        @dataclass
        class Dummy:
            text_list: List[str]
            text_dict: Dict[str, Decimal]
            optional_text: Optional[str]

        dummy_json_text = """
        {
            "text_list": ["a", "b", "c"],
            "text_dict": {
                "a": 1.0,
                "b": 2,
                "c": "3.3",
                "d": 2.2
            },
            "optional_text": "hello"
        }
        """

        dummy_json = json.loads(dummy_json_text)

        parsed = decode(dummy_json, Dummy)

        assert parsed.text_list == ["a", "b", "c"]
        assert parsed.text_dict["a"] == Decimal("1.0")
        assert parsed.text_dict["b"] == Decimal("2.0")
        assert parsed.text_dict["c"] == Decimal("3.3")
        assert parsed.text_dict["d"].quantize(Decimal("1.0")) == Decimal("2.2")
        assert parsed.optional_text == "hello"

    def test_nested_dataclass(self) -> None:
        @dataclass
        class NestedDummy:
            text: str
            number: Decimal

            boolean: bool

        @dataclass
        class Dummy:
            text_list: List[str]
            text_dict: Dict[str, Decimal]
            nested: NestedDummy

        dummy_json_text = """
        {

            "text_list": ["a", "b", "c"],
            "text_dict": {
                "a": 1.0,
                "b": 2,
                "c": "3.3",
                "d": 2.2
            },
            "nested": {
                "text": "hello",
                "number": 1.1,
                "boolean": true
            }
        }
        """

        dummy_json = json.loads(dummy_json_text)

        parsed = decode(dummy_json, Dummy)

        assert parsed.text_list == ["a", "b", "c"]
        assert parsed.text_dict["a"] == Decimal("1.0")
        assert parsed.text_dict["b"] == Decimal("2.0")
        assert parsed.text_dict["c"] == Decimal("3.3")
        assert parsed.text_dict["d"].quantize(Decimal("1.0")) == Decimal("2.2")
        assert parsed.nested.text == "hello"
        assert parsed.nested.number.quantize(Decimal("1.0")) == Decimal("1.1")
        assert parsed.nested.boolean is True

    def test_raise_when_type_not_mapped(self) -> None:
        with pytest.raises(ValueError):

            class NonMappedDummy:
                pass

            @dataclass
            class Dummy:
                text: str
                non_mapped: NonMappedDummy

            dummy_json_text = """
            {
                "text": "hello",
                "non_mapped": {}
            }
            """

            dummy_json = json.loads(dummy_json_text)

            decode(dummy_json, Dummy)

    def test_raise_when_missing_field(self) -> None:
        with pytest.raises(LocatedValidationErrorCollection):

            @dataclass
            class Dummy:
                text: int

            dummy_json_text = """
            {
            }
            """

            dummy_json = json.loads(dummy_json_text)

            decode(dummy_json, Dummy)

    def test_get_class_or_type_name(self) -> None:
        @dataclass
        class Dummy:
            text: str

        class NormalClass:
            pass

        assert get_class_or_type_name(Dummy) == "Dummy"
        assert get_class_or_type_name(List) == "typing.List"
        assert get_class_or_type_name(
            NormalClass
        ) == "{cls_name}.{method_name}.<locals>.NormalClass".format(
            cls_name=TestJsonDeserializerCodec.__name__,
            method_name=TestJsonDeserializerCodec.test_get_class_or_type_name.__name__,
        )

    def test_type_not_in_union(self) -> None:
        with pytest.raises(LocatedValidationErrorCollection):

            @dataclass
            class Dummy:
                text: Union[List[str], Dict[str, str]]

            dummy_json_text = """
            {
                "text": 1
            }

            """

            dummy_json = json.loads(dummy_json_text)

            decode(dummy_json, Dummy)

    def test_dict_with_wrong_type(self) -> None:
        with pytest.raises(LocatedValidationErrorCollection) as e:

            @dataclass
            class Dummy:
                text: Dict[int, int]

            dummy_json_text = """
            {
                "text": {
                    "a": "1"
                }
            }

            """

            dummy_json = json.loads(dummy_json_text)

            decode(dummy_json, Dummy)

        assert e.value is not None

    def test_enum(self) -> None:
        class MyEnum(Enum):
            A = "A"
            B = "B"

        @dataclass
        class Dummy:
            my_enum: MyEnum

        dummy_json_text = """
        {
            "my_enum": "A"
        }

        """

        dummy_json = json.loads(dummy_json_text)

        a = decode(dummy_json, Dummy)

        assert a.my_enum == MyEnum.A

    def test_enum_with_wrong_value(self) -> None:
        with pytest.raises(LocatedValidationErrorCollection):

            class MyEnum(Enum):
                A = "A"
                B = "B"

            @dataclass
            class Dummy:
                my_enum: MyEnum

            dummy_json_text = """
            {
                "my_enum": "C"
            }

            """

            dummy_json = json.loads(dummy_json_text)

            decode(dummy_json, Dummy)

    def test_date(self) -> None:
        @dataclass
        class Dummy:
            date_time: datetime
            date_: date
            time_: time

        dummy_json_text = """
        {
            "date_": "2020-01-01",
            "date_time": "2020-01-01T00:00:00+00:00",
            "time_": "00:00:00"
        }

        """

        dummy_json = json.loads(dummy_json_text)

        a = decode(dummy_json, Dummy)

        assert a.date_ == date(2020, 1, 1)
        assert a.date_time == datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert a.time_ == time(0, 0, 0)

    def test_date_with_wrong_value(self) -> None:
        with pytest.raises(LocatedValidationErrorCollection):

            @dataclass
            class Dummy:
                date_time: datetime

            dummy_json_text = """
                {
                    "date_time": "2020-01-01T00:00:00"
                }
    
                """

            dummy_json = json.loads(dummy_json_text)

            decode(dummy_json, Dummy)

    def test_primitive_class_inheritance(self) -> None:
        class MyInt(int):
            pass

        @dataclass
        class Dummy:
            my_int: MyInt

        dummy_json_text = """
        {
            "my_int": 1
        }

        """

        dummy_json = json.loads(dummy_json_text)

        a = decode(dummy_json, Dummy)

        assert a.my_int == MyInt(1)

    def test_primitive_class_inheritance_class_match(self) -> None:
        class MyInt(int):
            pass

        @dataclass
        class Dummy:
            my_int: MyInt

        dummy_json_text = """
        {
            "my_int": "1"
        }

        """

        dummy_json = json.loads(dummy_json_text)

        parsed = decode(dummy_json, Dummy)

        assert parsed.my_int == MyInt(1)
        assert isinstance(parsed.my_int, MyInt)

    def test_decode_newtype(self) -> None:
        UserId = NewType("UserId", int)

        assert decode(json.loads("1"), UserId) == UserId(1)
        assert isinstance(decode(json.loads("1"), UserId), int)

    def test_encode_and_decode_bytes(self):

        hello_bytes = b"hello"

        base64_hello_bytes = base64.b64encode(hello_bytes).decode("utf-8")

        assert encode(hello_bytes) == base64_hello_bytes

        assert decode(base64_hello_bytes, bytes) == hello_bytes

        @dataclass
        class Dummy:
            bytes_: bytes

        dummy_json_text = """
        {
            "bytes_": "aGVsbG8="
        }
        """

        dummy_json = json.loads(dummy_json_text)

        parsed = decode(dummy_json, Dummy)

        assert parsed.bytes_ == hello_bytes
