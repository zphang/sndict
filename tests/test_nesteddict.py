import collections as col

from sndict.nesteddict import NestedDict
from sndict.utils import list_equal


dict_a = col.OrderedDict([
    ("key1", "val1"),
    ("key2", col.OrderedDict([
        ("key2_1", "val2_1"),
        ("key2_2", "val2_2"),
    ])),
    ("key3", col.OrderedDict([
        ("key3_1", col.OrderedDict([
            ("key3_1_1", "val3_1_1"),
            ("key3_1_2", "val3_1_2"),
        ])),
        ("key3_2", col.OrderedDict([
            ("key3_2_1", "val3_2_1"),
        ])),
    ])),
])

dict_data_b = [
    (("key_b",), "val_b"),
    (("key_a", "key_a_b"), "val_a_b"),
    (("key_a", "key_a_a"), "val_a_a"),
]

empty_dict = col.OrderedDict()


def test_from_flat():
    assert list_equal(
        NestedDict.from_flat(dict_data_b).keys(),
        ['key_b', 'key_a'],
    )


def test_flatten_keys():
    assert list_equal(
        NestedDict(dict_a).flatten_keys(),
        [('key1',),
         ('key2', 'key2_1'),
         ('key2', 'key2_2'),
         ('key3', 'key3_1', 'key3_1_1'),
         ('key3', 'key3_1', 'key3_1_2'),
         ('key3', 'key3_2', 'key3_2_1')]
    )
    assert list_equal(
        NestedDict(dict_a).flatten_keys(max_depth=1),
        [('key1',), ('key2',), ('key3',)],
    )
    assert list_equal(
        NestedDict(empty_dict).flatten_keys(),
        list(),
    )


def test_flatten_values():
    assert list_equal(
        NestedDict(dict_a).flatten_values(),
        ['val1', 'val2_1', 'val2_2', 'val3_1_1', 'val3_1_2', 'val3_2_1'],
    )
    flattened_one_level = NestedDict(dict_a).flatten_values(max_depth=1)
    assert flattened_one_level[0] == 'val1'
    assert isinstance(flattened_one_level[1], col.OrderedDict)
    assert isinstance(flattened_one_level[2], col.OrderedDict)

    assert list_equal(
        NestedDict(empty_dict).flatten_values(),
        list(),
    )


def test_filter_values():
    assert list_equal(
        NestedDict.from_flat(dict_data_b)
            .filter_values(lambda _: _[-1] == "b")
            .flatten_keys(),
        [('key_b',), ('key_a', 'key_a_b')],
    )


def test_nested_set_and_get():
    ndict = NestedDict(dict_a)
    assert ndict.has_nested_key(('key3', 'key3_2', 'key3_2_1'))
    assert not ndict.has_nested_key(('keyX', 'keyX_1', 'keyX_1_1'))

    ndict.nested_set(('keyX', 'keyX_1', 'keyX_1_1'), "valX_1_1")
    assert ndict.has_nested_key(('keyX', 'keyX_1', 'keyX_1_1'))
    assert ndict.nested_get(('keyX', 'keyX_1', 'keyX_1_1')) == "valX_1_1"


def test_nested_update():
    ndict = NestedDict(dict_a)
    ndict.nested_update({'keyX': {'keyX_1': {'keyX_1_1': 'valX_1_1'}}})
    assert ndict.nested_get(('keyX', 'keyX_1', 'keyX_1_1')) == "valX_1_1"


def test_ix():
    ndict = NestedDict(dict_a)
    assert ndict.ix['key3', 'key3_2', 'key3_2_1'] == "val3_2_1"
    assert isinstance(ndict.ix['key3'], dict)
    try:
        _ = ndict.ix['keyX', 'keyX_1', 'keyX_1_1']
        raise RuntimeError
    except KeyError:
        pass

    ndict.ix['keyX', 'keyX_1', 'keyX_1_1'] = "valX_1_1"
    assert ndict.ix['keyX', 'keyX_1', 'keyX_1_1'] == "valX_1_1"


def test_convert():
    converted_b = NestedDict(dict_a).convert()
    assert isinstance(converted_b, NestedDict)
    assert isinstance(converted_b.values()[1], NestedDict)
    assert isinstance(converted_b.values()[2].values()[0], NestedDict)

    converted_b = NestedDict(dict_a).convert("odict")
    assert isinstance(converted_b, col.OrderedDict)
    assert isinstance(converted_b.values()[1], col.OrderedDict)
    assert isinstance(converted_b.values()[2].values()[0], col.OrderedDict)

    assert isinstance(NestedDict(empty_dict).convert(), NestedDict)
    assert list_equal(
        NestedDict.from_flat(dict_data_b)
            .sort_nested_keys().flatten_keys(),
        [('key_a', 'key_a_a'), ('key_a', 'key_a_b'), ('key_b',)],
    )


def test_to_tree_string():
    assert NestedDict(dict_a).to_tree_string("o-", val_mode="repr") == \
       "key1: 'val1'\nkey2:\n'-key2_1: 'val2_1'\n'-key2_2: " \
       "'val2_2'\nkey3:\n'-key3_1:\n  '-key3_1_1: 'val3_1_1'\n  " \
       "'-key3_1_2: 'val3_1_2'\n'-key3_2:\n  '-key3_2_1: 'val3_2_1'\n"
