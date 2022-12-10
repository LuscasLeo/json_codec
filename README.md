# Json Codec

It's a simple library to encode and decode json to strict python types using dataclasses and builtin python types.

## Installation

```bash
pip install json-codec

poetry add json-codec
```

## Usage

### Parse a simple primitive type

```python
from json_codec import decode
import json

assert decode(json.loads("true"), bool) is True
assert decode(json.loads("false"), bool) is False
assert decode(json.loads("null"), Optional[bool]) is None
assert decode(json.loads("1"), int) == 1
assert decode(json.loads("1"), Decimal) == Decimal("1")
assert decode(json.loads('"1.1"'), Decimal) == Decimal("1.1")
assert decode(json.loads('"1.1"'), float) == 1.1
assert decode(json.loads('"1.1"'), str) == "1.1"

assert decode(json.loads('[1,1]'), List[int]) == [1, 1]
```

### Parse a dataclass

```python
from dataclasses import dataclass
from json_codec import decode
import json

@dataclass(frozen=True)
class User:
    name: str
    age: int

assert decode({"name": "John", "age": 30}, User) == User(name="John", age=30)


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
```

### Parse a dataclass with a nested dataclass

```python
from dataclasses import dataclass
from json_codec import decode
import json

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
```

### Parse a newtype

```python
from json_codec import decode
from typing import NewType
import json

UserId = NewType("UserId", int)

assert decode(json.loads("1"), UserId) == UserId(1)
assert isinstance(decode(json.loads("1"), UserId), int)

```