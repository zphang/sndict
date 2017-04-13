import collections as col
from nose.tools import assert_raises

from sndict.structurednesteddict import StructuredNestedDict, LevelError
from sndict.utils import list_equal, strip_spaces


dict_a = col.OrderedDict([
    ("key1", col.OrderedDict([
        ("key1_1", col.OrderedDict([
            ("key1_1_1", "val1_1_1"),
            ("key1_1_2", "val1_1_2"),
        ])),
    ])),
    ("key2", col.OrderedDict([
        ("key2_1", col.OrderedDict([
            ("key2_1_1", "val2_1_1"),
            ("key2_1_2", "val2_1_2"),
        ])),
        ("key2_2", col.OrderedDict([
            ("key2_2_1", "val2_2_1"),
        ])),
    ])),
    ("key3", col.OrderedDict()),
])


dict_b = col.OrderedDict([
    ("key1", col.OrderedDict([
        ("keyX_1", col.OrderedDict([
            ("keyX_X_1", "val1_1_1"),
            ("keyX_X_2", "val1_1_2"),
        ])),
    ])),
    ("key2", col.OrderedDict([
        ("keyX_1", col.OrderedDict([
            ("keyX_X_1", "val2_1_1"),
            ("keyX_X_2", "val2_1_2"),
        ])),
        ("keyX_1", col.OrderedDict([
            ("keyX_X_1", "val2_2_1"),
            ("keyX_X_2", "val2_2_2"),
            ("keyX_X_3", "val2_2_3"),
            ("keyX_X_4", "val2_2_4"),
            ("keyX_X_5", "val2_2_5"),
        ])),
    ])),
    ("key3", col.OrderedDict()),
])


dict_c = col.OrderedDict([
    ("key1", col.OrderedDict([
        ("keyX_1", col.OrderedDict([
            ("keyX_X_1", "val1_1_1"),
            ("keyX_X_2", "val1_1_2"),
        ])),
    ])),
    ("key2", col.OrderedDict([
        ("keyX_1", col.OrderedDict([
            ("keyX_X_1", "val2_1_1"),
            ("keyX_X_2", "val2_1_2"),
        ])),
        ("keyX_2", col.OrderedDict([
            ("keyX_X_1", "val2_2_1"),
            ("keyX_X_2", "val2_2_2"),
            ("keyX_X_3", "val2_2_3"),
            ("keyX_X_4", "val2_2_4"),
            ("keyX_X_5", "val2_2_5"),
        ])),
    ])),
    ("key3", col.OrderedDict()),
])


def test_dim():
    assert StructuredNestedDict(dict_a, levels=1).dim == (3,)
    assert StructuredNestedDict(dict_a, levels=2).dim == (3, 3)
    assert StructuredNestedDict(dict_a, levels=3).dim == (3, 3, 5)


def test_iterflatten():
    sndict = StructuredNestedDict(dict_a, levels=3)
    assert list_equal(
        col.OrderedDict(sndict.iterflatten(1)).keys(),
        [('key1', 'key1_1'), ('key2', 'key2_1'), ('key2', 'key2_2')]
    )
    assert list_equal(
        col.OrderedDict(sndict.iterflatten(2)).values(),
        ['val1_1_1', 'val1_1_2', 'val2_1_1', 'val2_1_2', 'val2_2_1'],
    )
    assert list_equal(
        col.OrderedDict(sndict.iterflatten(-2)).keys(),
        col.OrderedDict(sndict.iterflatten(1)).keys(),
    )
    assert list_equal(
        col.OrderedDict(sndict.iterflatten(-1)).keys(),
        col.OrderedDict(sndict.iterflatten(2)).keys(),
    )


def test_flatten():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    assert named_sndict_a.flatten(0).dim == named_sndict_a.dim
    assert named_sndict_a.flatten(1).dim == (3, 5)
    assert list_equal(
        map(tuple, named_sndict_a.flatten(1).keys()),
        [('key1', 'key1_1'), ('key2', 'key2_1'), ('key2', 'key2_2')],
    )
    assert named_sndict_a.flatten(1).level_names == ("a___b", "c")
    assert_raises(LevelError, named_sndict_a.flatten, 3)
    assert len(named_sndict_a.flatten_keys()) == named_sndict_a.dim[-1]


def test_unique_keys():
    sndict_b = StructuredNestedDict(dict_b, levels=3)
    assert list_equal(
        map(tuple, sndict_b.unique_keys()),
        [('key1', 'key2', 'key3'),
         ('keyX_1',),
         ('keyX_X_1', 'keyX_X_2', 'keyX_X_3', 'keyX_X_4', 'keyX_X_5')],
    )


def test_stratify():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    flattened_stratified_named_sndict_a = named_sndict_a\
        .flatten(1, named=True).stratify(1)
    assert list_equal(
        flattened_stratified_named_sndict_a.level_names,
        ["a", "b", "c"]
    )
    assert flattened_stratified_named_sndict_a.dim == (2, 3, 5)
    assert flattened_stratified_named_sndict_a


def test_rearrange():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    assert list_equal(
        named_sndict_a.rearrange([1, 0]).flatten_keys(2, named=False),
        [('key1_1', 'key1', 'key1_1_1'),
         ('key1_1', 'key1', 'key1_1_2'),
         ('key2_1', 'key2', 'key2_1_1'),
         ('key2_1', 'key2', 'key2_1_2'),
         ('key2_2', 'key2', 'key2_2_1')],
    )
    assert named_sndict_a.rearrange([1, 0]).level_names \
        == ("b", "a", "c")
    assert named_sndict_a.rearrange([0, 1]).level_names \
        == ("a", "b", "c")

    assert list_equal(
        named_sndict_a\
            .rearrange(["c", "b", "a"])\
            .flatten_keys(2, named=False),
        [('key1_1_1', 'key1_1', 'key1'),
         ('key1_1_2', 'key1_1', 'key1'),
         ('key2_1_1', 'key2_1', 'key2'),
         ('key2_1_2', 'key2_1', 'key2'),
         ('key2_2_1', 'key2_2', 'key2')],
    )
    assert named_sndict_a.rearrange(["c", "b", "a"]).level_names \
        == ("c", "b", "a")

    unnamed_sndict_a = StructuredNestedDict(
        dict_a, levels=3)
    assert unnamed_sndict_a.rearrange([2, 1, 0]).levels == 3
    assert unnamed_sndict_a.rearrange([2, 1, 0])\
        .flatten_keys(2, named=False)[0] == ('key1_1_1', 'key1_1', 'key1')


def test_swap_levels():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    assert named_sndict_a.swap_levels("c", "a").level_names == \
        ("c", "b", "a")


def test_replace_metadata():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])

    named_sndict_a2 = named_sndict_a.replace_metadata(levels=2)
    assert named_sndict_a2.levels == 2
    assert_raises(LevelError, named_sndict_a2.flatten, 2)

    named_sndict_a2 = named_sndict_a.replace_metadata(
        levels=3, level_names=["A", "B", "C"])
    assert named_sndict_a2.level_names == ("A", "B", "C")


def test_sort_keys():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    assert list_equal(
        named_sndict_a.sort_keys(reverse=True).keys(),
        ['key3', 'key2', 'key1'],
    )


def test_sort_values():
    assert list_equal(
        StructuredNestedDict({"a": "z", "b": "y", "c": "x"})
            .sort_values().values(),
        ["x", "y", "z"],
    )


def test_map_values():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    assert list_equal(
        named_sndict_a.map_values(str.upper).flatten_values(),
        ['VAL1_1_1', 'VAL1_1_2', 'VAL2_1_1', 'VAL2_1_2', 'VAL2_2_1']
    )


def test_filter_key():
    sndict_a = StructuredNestedDict(dict_a, levels=3)
    sndict_c = StructuredNestedDict(dict_c, levels=3)
    assert list_equal(
        sndict_a.filter_key(["key1"]).keys(),
        ['key1']
    )
    assert list_equal(
        sndict_a.filter_key([["key1", "key3"]]).keys(),
        ['key1', 'key3'],
    )
    assert list_equal(
        sndict_a.filter_key([["key1", "key3"]], drop_empty=True).keys(),
        ['key1'],
    )
    assert list_equal(
        sndict_a.filter_key([slice(None), "key1_1"]).flatten_values(),
        ['val1_1_1', 'val1_1_2'],
    )
    assert list_equal(
        sndict_a.filter_key({"level1": "key1_1"}).flatten_values(),
        ['val1_1_1', 'val1_1_2'],
    )
    assert list_equal(
        sndict_c.filter_key({"level1": "keyX_1"}).flatten_values(),
        ['val1_1_1', 'val1_1_2', 'val2_1_1', 'val2_1_2'],
    )


def test_filter_values():
    sndict_c = StructuredNestedDict(dict_c, levels=3)
    assert list_equal(
        sndict_c.filter_values(lambda _: _[-1] == "2")
            .flatten_keys(1, named=False),
        [('key1', 'keyX_1'), ('key2', 'keyX_1'), ('key2', 'keyX_2')],
    )


def test_nested_set_and_get():
    sndict = StructuredNestedDict(dict_a, levels=3)
    assert sndict.has_nested_key(('key1', 'key1_1', 'key1_1_1'))
    assert not sndict.has_nested_key(('keyX', 'keyX_1', 'keyX_1_1'))

    sndict.nested_set(('keyX', 'keyX_1', 'keyX_1_1'), "valX_1_1")
    assert sndict.has_nested_key(('keyX', 'keyX_1', 'keyX_1_1'))
    assert sndict.nested_get(('keyX', 'keyX_1', 'keyX_1_1')) == "valX_1_1"


def test_ix():
    sndict_a = StructuredNestedDict(dict_a, levels=3)
    assert sndict_a.ix['key1', 'key1_1', 'key1_1_1'] == "val1_1_1"
    try:
        _ = sndict_a.ix['keyX', 'keyX_1', 'keyX_1_1']
        raise RuntimeError
    except KeyError:
        pass

        sndict_a.ix['keyX', 'keyX_1', 'keyX_1_1'] = "valX_1_1"
    assert sndict_a.ix['keyX', 'keyX_1', 'keyX_1_1'] == "valX_1_1"

    sndict_c = StructuredNestedDict(dict_c, levels=3)
    sndict_c.ix[:, "keyX_1", :] = "NEW"
    assert list_equal(
        sndict_c.flatten_values(),
        ['NEW', 'NEW', 'NEW', 'NEW',
         'val2_2_1', 'val2_2_2', 'val2_2_3', 'val2_2_4', 'val2_2_5'],
    )


def test__delitem__():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    del named_sndict_a["key2"]
    assert list_equal(
        named_sndict_a.flatten_values(),
        ['val1_1_1', 'val1_1_2'],
    )
    assert named_sndict_a.dim == (2, 1, 2)


def test__setitem__():
    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    named_sndict_a["newkey"] = {}
    assert named_sndict_a.dim == (4, 3, 5)
    assert named_sndict_a["newkey"].levels == 2
    assert named_sndict_a["newkey"].level_names == ("b", "c")

    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    try:
        named_sndict_a["newkey"] = {1: 1}
        raise Exception
    except TypeError:
        pass

    named_sndict_a = StructuredNestedDict(
        dict_a, levels=3, level_names=["a", "b", "c"])
    named_sndict_a["newkey"] = {1: {2: 3, 4: 5}}
    assert named_sndict_a.dim == (4, 4, 7)
    assert named_sndict_a["newkey"].levels == 2
    assert named_sndict_a["newkey"].level_names == ("b", "c")


def test_str():
    assert strip_spaces(str(StructuredNestedDict(dict_a, levels=2))) == \
        "StructuredNestedDict({'key1':{'key1_1':{'key1_1_1':'val1_1_1'," \
        "'key1_1_2':'val1_1_2',},},'key2':{'key2_1':{'key2_1_1':'val2_1_1'," \
        "'key2_1_2':'val2_1_2',},'key2_2':{'key2_2_1':'val2_2_1',},}," \
        "'key3':{},},levels=2)"

    assert strip_spaces(str(
        StructuredNestedDict(dict_a, levels=2, level_names=["a", "b"])
    )) == "StructuredNestedDict({'key1':{'key1_1':{'key1_1_1':'val1_1_1'," \
          "'key1_1_2':'val1_1_2',},},'key2':{'key2_1':{'key2_1_1':'val2_1_1'," \
          "'key2_1_2':'val2_1_2',},'key2_2':{'key2_2_1':'val2_2_1',},}," \
          "'key3':{},},levels=2,level_names=('a','b'))"


def test_to_tree_string():
    assert StructuredNestedDict(dict_a, levels=3).to_tree_string() == \
        "key1:\n'-key1_1:\n  '-key1_1_1: <type 'str'>\n  " \
        "'-key1_1_2: <type 'str'>\nkey2:\n'-key2_1:\n  " \
        "'-key2_1_1: <type 'str'>\n  '-key2_1_2: <type 'str'>\n" \
        "'-key2_2:\n  '-key2_2_1: <type 'str'>\nkey3:\n"
