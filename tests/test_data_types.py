import uuid
import decimal
import fractions
import collections
from enum import Enum
from datetime import datetime, date, time, timedelta, timezone
from dataclasses import dataclass, InitVar
from queue import Queue
from pathlib import Path
from typing import (
    Hashable,
    List,
    Deque,
    Tuple,
    Set,
    FrozenSet,
    MutableSet,
    ChainMap,
    Dict,
    Mapping,
    MutableMapping,
    Sequence,
    Optional,
    Any,
    AnyStr,
    Union,
    TypeVar,
    ClassVar,
)

from mashumaro import DataClassDictMixin
from mashumaro.exceptions import UnserializableField, UnserializableDataError,\
    MissingField
from mashumaro.types import RoundedDecimal, SerializableType,\
    SerializationStrategy
from .utils import same_types
from .entities import (
    MyEnum,
    MyIntEnum,
    MyFlag,
    MyIntFlag,
    MyDataClass,
    MutableString,
)

import pytest


class Fixture:
    INT = 123
    FLOAT = 1.23
    BOOL = True
    LIST = [1, 2, 3]
    TUPLE = (1, 2, 3)
    DEQUE = collections.deque([1, 2, 3])
    SET = {1, 2, 3}
    FROZEN_SET = frozenset([1, 2, 3])
    CHAIN_MAP = collections.ChainMap({'a': 1, 'b': 2}, {'c': 3, 'd': 4})
    MAPS_LIST = [{'a': 1, 'b': 2}, {'c': 3, 'd': 4}]
    DICT = {'a': 1, 'b': 2}
    BYTES = b'123'
    BYTES_BASE64 = 'MTIz\n'
    BYTE_ARRAY = bytearray(b'123')
    STR = '123'
    ENUM = MyEnum.a
    INT_ENUM = MyIntEnum.a
    FLAG = MyFlag.a
    INT_FLAG = MyIntFlag.a
    DATA_CLASS = MyDataClass(a=1, b=2)
    NONE = None
    DATETIME = datetime(2018, 10, 29, 12, 46, 55, 308495)
    DATE = DATETIME.date()
    TIME = DATETIME.time()
    TIMEDELTA = timedelta(3.14159265358979323846)
    TIMEZONE = timezone(timedelta(hours=3))
    UUID = uuid.UUID('3c25dd74-f208-46a2-9606-dd3919e975b7')
    UUID_STR = '3c25dd74-f208-46a2-9606-dd3919e975b7'
    DECIMAL = decimal.Decimal('1.33')
    DECIMAL_STR = '1.33'
    FRACTION = fractions.Fraction('1/3')
    FRACTION_STR = '1/3'
    MUTABLE_STRING = MutableString(STR)
    MUTABLE_STRING_STR = STR
    PATH = Path('.')
    PATH_STR = '.'


inner_values = [
    (int, Fixture.INT, Fixture.INT),
    (float, Fixture.FLOAT, Fixture.FLOAT),
    (bool, Fixture.BOOL, Fixture.BOOL),
    (List[int], Fixture.LIST, Fixture.LIST),
    (Deque[int], Fixture.DEQUE, Fixture.LIST),
    (Tuple[int], Fixture.TUPLE, Fixture.LIST),
    (Set[int], Fixture.SET, Fixture.LIST),
    (FrozenSet[int], Fixture.FROZEN_SET, Fixture.LIST),
    (ChainMap[str, int], Fixture.CHAIN_MAP, Fixture.MAPS_LIST),
    (Dict[str, int], Fixture.DICT, Fixture.DICT),
    (Mapping[str, int], Fixture.DICT, Fixture.DICT),
    (MutableMapping[str, int], Fixture.DICT, Fixture.DICT),
    (Sequence[int], Fixture.LIST, Fixture.LIST),
    (bytes, Fixture.BYTES, Fixture.BYTES),
    (bytearray, Fixture.BYTE_ARRAY, Fixture.BYTE_ARRAY),
    (str, Fixture.STR, Fixture.STR),
    (MyEnum, Fixture.ENUM, Fixture.ENUM),
    (MyIntEnum, Fixture.INT_ENUM, Fixture.INT_ENUM),
    (MyFlag, Fixture.FLAG, Fixture.FLAG),
    (MyIntFlag, Fixture.INT_FLAG, Fixture.INT_FLAG),
    (MyDataClass, Fixture.DATA_CLASS, Fixture.DICT),
    (type(None), Fixture.NONE, Fixture.NONE),
    (datetime, Fixture.DATETIME, Fixture.DATETIME),
    (date, Fixture.DATE, Fixture.DATE),
    (time, Fixture.TIME, Fixture.TIME),
    (timedelta, Fixture.TIMEDELTA, Fixture.TIMEDELTA.total_seconds()),
    (timezone, Fixture.TIMEZONE, 'UTC+03:00'),
    (uuid.UUID, Fixture.UUID, Fixture.UUID_STR),
    (decimal.Decimal, Fixture.DECIMAL, Fixture.DECIMAL_STR),
    (fractions.Fraction, Fixture.FRACTION, Fixture.FRACTION_STR),
    (MutableString, Fixture.MUTABLE_STRING, Fixture.MUTABLE_STRING_STR),
    (Path, Fixture.PATH, Fixture.PATH_STR)
]


hashable_inner_values = [
    (type_, value, value_dumped) for type_, value, value_dumped in inner_values
    if isinstance(value, Hashable) and isinstance(value_dumped, Hashable)
]


generic_sequence_types = [List, Deque, Tuple, Set, FrozenSet]
generic_mapping_types = [Dict, Mapping, MutableMapping]


unsupported_field_types = [
    list, collections.deque, tuple, set, frozenset,
    collections.ChainMap, dict, Queue]


T = TypeVar('T', int, str)
unsupported_typing_primitives = [AnyStr, Union[int, str], T]


x_factory_mapping = {
    List: list,
    Deque: collections.deque,
    Tuple: tuple,
    Set: set,
    FrozenSet: frozenset,
    MutableSet: set,
    Dict: lambda items: {k: v for k, v in items},
    Mapping: lambda items: {k: v for k, v in items},
    MutableMapping: lambda items: {k: v for k, v in items},
    ChainMap: lambda items: collections.ChainMap(*({k: v} for k, v in items))
}


# noinspection PyCallingNonCallable
def check_one_arg_generic(type_, value_info, use_bytes, use_enum, use_datetime):
    x_type, x_value, x_value_dumped = value_info

    @dataclass
    class DataClass(DataClassDictMixin):
        x: type_[x_type]

    x_factory = x_factory_mapping[type_]
    x = x_factory([x_value for _ in range(3)])
    instance = DataClass(x)
    if x_value_dumped is Fixture.BYTES:
        v_dumped = Fixture.BYTES if use_bytes else Fixture.BYTES_BASE64
    elif x_value_dumped is Fixture.BYTE_ARRAY:
        v_dumped = Fixture.BYTE_ARRAY if use_bytes else Fixture.BYTES_BASE64
    elif isinstance(x_value_dumped, Enum):
        v_dumped = x_value_dumped if use_enum else x_value_dumped.value
    elif isinstance(x_value_dumped, (datetime, date, time)):
        v_dumped = x_value_dumped if use_datetime \
            else x_value_dumped.isoformat()
    else:
        v_dumped = x_value_dumped
    dumped = {'x': list(x_factory([v_dumped for _ in range(3)]))}
    instance_dumped = instance.to_dict(
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    instance_loaded = DataClass.from_dict(
        dumped,
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    assert instance_dumped == dumped
    assert instance_loaded == instance
    instance_dumped = instance.to_dict(
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    instance_loaded = DataClass.from_dict(
        dumped,
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    assert same_types(instance_dumped, dumped)
    assert same_types(instance_loaded.x, x)


# noinspection PyCallingNonCallable
def check_two_args_generic(type_, key_info, value_info, use_bytes, use_enum,
                           use_datetime):
    k_type, k_value, k_value_dumped = key_info
    v_type, v_value, v_value_dumped = value_info

    @dataclass
    class DataClass(DataClassDictMixin):
        x: type_[k_type, v_type]

    x_factory = x_factory_mapping[type_]
    x = x_factory([(k_value, v_value) for _ in range(3)])
    instance = DataClass(x)
    if k_value_dumped is Fixture.BYTES:
        k_dumped = Fixture.BYTES if use_bytes else Fixture.BYTES_BASE64
    # Fixture.BYTE_ARRAY is not hashable
    # elif k_value_dumped is Fixture.BYTE_ARRAY:
    #     k_dumped = Fixture.BYTE_ARRAY if use_bytes else Fixture.BYTES_BASE64
    elif isinstance(k_value_dumped, Enum):
        k_dumped = k_value_dumped if use_enum else k_value_dumped.value
    elif isinstance(k_value_dumped, (datetime, date, time)):
        k_dumped = k_value_dumped if use_datetime \
            else k_value_dumped.isoformat()
    else:
        k_dumped = k_value_dumped
    if v_value_dumped is Fixture.BYTES:
        v_dumped = Fixture.BYTES if use_bytes else Fixture.BYTES_BASE64
    elif v_value_dumped is Fixture.BYTE_ARRAY:
        v_dumped = Fixture.BYTE_ARRAY if use_bytes else Fixture.BYTES_BASE64
    elif isinstance(v_value_dumped, Enum):
        v_dumped = v_value_dumped if use_enum else v_value_dumped.value
    elif isinstance(v_value_dumped, (datetime, date, time)):
        v_dumped = v_value_dumped if use_datetime \
            else v_value_dumped.isoformat()
    else:
        v_dumped = v_value_dumped
    if type_ is ChainMap:
        dumped = {'x': x_factory([(k_dumped, v_dumped) for _ in range(3)]).maps}
    else:
        dumped = {'x': x_factory([(k_dumped, v_dumped) for _ in range(3)])}
    instance_dumped = instance.to_dict(
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    instance_loaded = DataClass.from_dict(
        dumped,
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    assert instance_dumped == dumped
    assert instance_loaded == instance
    instance_dumped = instance.to_dict(
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    instance_loaded = DataClass.from_dict(
        dumped,
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    assert same_types(instance_dumped, dumped)
    assert same_types(instance_loaded.x, x)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
def test_one_level(value_info, use_bytes, use_enum, use_datetime):
    x_type, x_value, x_value_dumped = value_info

    @dataclass
    class DataClass(DataClassDictMixin):
        x: x_type

    instance = DataClass(x_value)
    if x_value_dumped is Fixture.BYTES:
        v_dumped = Fixture.BYTES if use_bytes else Fixture.BYTES_BASE64
    elif x_value_dumped is Fixture.BYTE_ARRAY:
        v_dumped = Fixture.BYTE_ARRAY if use_bytes else Fixture.BYTES_BASE64
    elif isinstance(x_value_dumped, Enum):
        v_dumped = x_value_dumped if use_enum else x_value_dumped.value
    elif isinstance(x_value_dumped, (datetime, date, time)):
        v_dumped = x_value_dumped if use_datetime \
            else x_value_dumped.isoformat()
    else:
        v_dumped = x_value_dumped
    dumped = {'x': v_dumped}
    instance_dumped = instance.to_dict(
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    instance_loaded = DataClass.from_dict(
        dumped,
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    assert instance_dumped == dumped
    assert instance_loaded == instance
    instance_dumped = instance.to_dict(
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    instance_loaded = DataClass.from_dict(
        dumped,
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    assert same_types(instance_dumped, dumped)
    assert same_types(instance_loaded.x, x_value)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
def test_with_generic_list(value_info, use_bytes, use_enum, use_datetime):
    check_one_arg_generic(List, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
def test_with_generic_deque(value_info, use_bytes, use_enum, use_datetime):
    check_one_arg_generic(Deque, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
def test_with_generic_tuple(value_info, use_bytes, use_enum, use_datetime):
    check_one_arg_generic(Tuple, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', hashable_inner_values)
def test_with_generic_set(value_info, use_bytes, use_enum, use_datetime):
    check_one_arg_generic(Set, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', hashable_inner_values)
def test_with_generic_frozenset(value_info, use_bytes, use_enum, use_datetime):
    check_one_arg_generic(
        FrozenSet, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', hashable_inner_values)
def test_with_generic_mutable_set(
        value_info, use_bytes, use_enum, use_datetime):
    check_one_arg_generic(
        MutableSet, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
@pytest.mark.parametrize('key_info', hashable_inner_values)
def test_with_generic_dict(
        key_info, value_info, use_bytes, use_enum, use_datetime):
    check_two_args_generic(
        Dict, key_info, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
@pytest.mark.parametrize('key_info', hashable_inner_values)
def test_with_generic_mapping(
        key_info, value_info, use_bytes, use_enum, use_datetime):
    check_two_args_generic(
        Mapping, key_info, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
@pytest.mark.parametrize('key_info', hashable_inner_values)
def test_with_generic_mutable_mapping(
        key_info, value_info, use_bytes, use_enum, use_datetime):
    check_two_args_generic(
        MutableMapping, key_info, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
@pytest.mark.parametrize('key_info', hashable_inner_values)
def test_with_generic_chain_map(
        key_info, value_info, use_bytes, use_enum, use_datetime):
    check_two_args_generic(
        ChainMap, key_info, value_info, use_bytes, use_enum, use_datetime)


@pytest.mark.parametrize('x_type', unsupported_field_types)
@pytest.mark.parametrize('generic_type', generic_sequence_types)
def test_unsupported_generic_field_types(x_type, generic_type):
    with pytest.raises(UnserializableField):
        @dataclass
        class _(DataClassDictMixin):
            # noinspection PyTypeChecker
            x: generic_type[x_type]


@pytest.mark.parametrize('x_type', unsupported_typing_primitives)
@pytest.mark.parametrize('generic_type', generic_sequence_types)
def test_unsupported_generic_typing_primitives(x_type, generic_type):
    with pytest.raises(UnserializableDataError):
        @dataclass
        class _(DataClassDictMixin):
            # noinspection PyTypeChecker
            x: generic_type[x_type]


@pytest.mark.parametrize('x_type', unsupported_field_types)
def test_unsupported_field_types(x_type):
    with pytest.raises(UnserializableField):
        @dataclass
        class _(DataClassDictMixin):
            x: x_type


@pytest.mark.parametrize('x_type', unsupported_typing_primitives)
def test_unsupported_typing_primitives(x_type):
    with pytest.raises(UnserializableDataError):
        @dataclass
        class _(DataClassDictMixin):
            x: x_type


@pytest.mark.parametrize('generic_type', generic_mapping_types)
def test_data_class_as_mapping_key(generic_type):
    @dataclass
    class Key(DataClassDictMixin):
        pass
    with pytest.raises(UnserializableDataError):
        @dataclass
        class _(DataClassDictMixin):
            x: generic_type[Key, int]


def test_data_class_as_chain_map_key():
    @dataclass
    class Key(DataClassDictMixin):
        pass
    with pytest.raises(UnserializableDataError):
        @dataclass
        class _(DataClassDictMixin):
            x: ChainMap[Key, int]


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
def test_with_any(value_info, use_bytes, use_enum, use_datetime):
    @dataclass
    class DataClass(DataClassDictMixin):
        x: Any

    x = value_info[1]
    dumped = {'x': x}
    instance = DataClass(x)
    instance_dumped = instance.to_dict(
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    instance_loaded = DataClass.from_dict(
        dumped,
        use_bytes=use_bytes,
        use_enum=use_enum,
        use_datetime=use_datetime
    )
    assert instance_dumped == dumped
    assert instance_loaded == instance
    assert same_types(instance_dumped, dumped)
    assert same_types(instance_loaded.x, x)


@pytest.mark.parametrize('use_datetime', [True, False])
@pytest.mark.parametrize('use_enum', [True, False])
@pytest.mark.parametrize('use_bytes', [True, False])
@pytest.mark.parametrize('value_info', inner_values)
def test_with_optional(value_info, use_bytes, use_enum, use_datetime):
    x_type, x_value, x_value_dumped = value_info

    @dataclass
    class DataClass(DataClassDictMixin):
        x: Optional[x_type] = None

    for instance in [DataClass(x_value), DataClass()]:
        if instance.x is None:
            v_dumped = None
        elif x_value_dumped is Fixture.BYTES:
            v_dumped = Fixture.BYTES if use_bytes else Fixture.BYTES_BASE64
        elif x_value_dumped is Fixture.BYTE_ARRAY:
            v_dumped = Fixture.BYTE_ARRAY if use_bytes else Fixture.BYTES_BASE64
        elif isinstance(x_value_dumped, Enum):
            v_dumped = x_value_dumped if use_enum else x_value_dumped.value
        elif isinstance(x_value_dumped, (datetime, date, time)):
            v_dumped = x_value_dumped if use_datetime \
                else x_value_dumped.isoformat()
        else:
            v_dumped = x_value_dumped
        dumped = {'x': v_dumped}
        instance_dumped = instance.to_dict(
            use_bytes=use_bytes,
            use_enum=use_enum,
            use_datetime=use_datetime
        )
        instance_loaded = DataClass.from_dict(
            dumped,
            use_bytes=use_bytes,
            use_enum=use_enum,
            use_datetime=use_datetime
        )
        assert instance_dumped == dumped
        assert instance_loaded == instance
        instance_dumped = instance.to_dict(
            use_bytes=use_bytes,
            use_enum=use_enum,
            use_datetime=use_datetime
        )
        instance_loaded = DataClass.from_dict(
            dumped,
            use_bytes=use_bytes,
            use_enum=use_enum,
            use_datetime=use_datetime
        )
        assert same_types(instance_dumped, dumped)
        assert same_types(instance_loaded.x, instance.x)


def test_raises_missing_field():
    @dataclass
    class DataClass(DataClassDictMixin):
        x: int
    with pytest.raises(MissingField):
        DataClass.from_dict({})


def test_empty_dataclass():
    @dataclass
    class DataClass(DataClassDictMixin):
        pass
    assert DataClass().to_dict() == {}
    assert type(DataClass.from_dict({})) is DataClass
    assert DataClass.from_dict({}).__dict__ == {}


def test_weird_field_type():
    with pytest.raises(UnserializableDataError):
        @dataclass
        class _(DataClassDictMixin):
            x: 123


@pytest.mark.parametrize('rounding', [None, decimal.ROUND_UP,
                                      decimal.ROUND_DOWN])
@pytest.mark.parametrize('places', [None, 1, 2])
def test_rounded_decimal(places, rounding):
    @dataclass
    class DataClass(DataClassDictMixin):
        x: RoundedDecimal(places=places, rounding=rounding)
    digit = decimal.Decimal(0.35)
    if places is not None:
        exp = decimal.Decimal((0, (1,), -places))
        quantized = digit.quantize(exp, rounding)
    else:
        quantized = digit
    assert DataClass(digit).to_dict() == {'x': str(quantized)}
    assert DataClass.from_dict({'x': str(quantized)}) == DataClass(x=quantized)


def test_serializable_type():
    with pytest.raises(NotImplementedError):
        # noinspection PyTypeChecker
        SerializableType._serialize(None)
    with pytest.raises(NotImplementedError):
        SerializableType._deserialize(None)


def test_serialization_strategy():
    with pytest.raises(NotImplementedError):
        # noinspection PyTypeChecker
        SerializationStrategy._serialize(None, None)
    with pytest.raises(NotImplementedError):
        # noinspection PyTypeChecker
        SerializationStrategy._deserialize(None, None)


def test_class_vars():

    @dataclass
    class DataClass(DataClassDictMixin):
        x: ClassVar[int] = None

    assert DataClass().to_dict() == {}
    assert DataClass.from_dict({}) == DataClass()


def test_init_vars():

    @dataclass
    class DataClass(DataClassDictMixin):
        x: InitVar[int] = None
        y: int = None

        def __post_init__(self, x: int):
            if self.y is None and x is not None:
                self.y = x

    assert DataClass().to_dict() == {'y': None}
    assert DataClass(x=1).to_dict() == {'y': 1}
    assert DataClass.from_dict({}) == DataClass()
    assert DataClass.from_dict({'x': 1}) == DataClass()


def test_dataclass_with_defaults():

    @dataclass
    class DataClass(DataClassDictMixin):
        x: int
        y: int = 1

    assert DataClass.from_dict({'x': 0}) == DataClass(x=0, y=1)


def test_derived_dataclass_with_ancestors_defaults():

    @dataclass
    class A:
        x: int
        y: int = 1

    @dataclass
    class B(A, DataClassDictMixin):
        z: int = 3

    @dataclass
    class C(B, DataClassDictMixin):
        y: int = 4

    @dataclass
    class D(C):
        pass

    assert B.from_dict({'x': 0}) == B(x=0, y=1, z=3)
    assert C.from_dict({'x': 0}) == C(x=0, y=4, z=3)
    assert D.from_dict({'x': 0}) == D(x=0, y=4, z=3)
