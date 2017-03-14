import collections as col
from nose.tools import assert_raises

from dictplus.sndict import StructuredNestedDict, LevelError, _get_filter_func
from dictplus.utils import list_equal, strip_spaces


dict_b = col.OrderedDict([
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


def test_dim():
    assert StructuredNestedDict(dict_b, levels=1).dim == (3,)
    assert StructuredNestedDict(dict_b, levels=2).dim == (3, 3)
    assert StructuredNestedDict(dict_b, levels=3).dim == (3, 3, 5)


def test_iterflatten():
    sndict = StructuredNestedDict(dict_b, levels=3)
    assert list_equal(
        dict(sndict.iterflatten(1)).keys(),
        [('key1', 'key1_1'), ('key2', 'key2_2'), ('key2', 'key2_1')]
    )
    assert list_equal(
        dict(sndict.iterflatten(2)).values(),
        ['val1_1_2', 'val2_1_1', 'val2_1_2', 'val2_2_1', 'val1_1_1'],
    )
    assert list_equal(
        dict(sndict.iterflatten(-2)).keys(),
        dict(sndict.iterflatten(1)).keys(),
    )
    assert list_equal(
        dict(sndict.iterflatten(-1)).keys(),
        dict(sndict.iterflatten(2)).keys(),
    )


def test_flatten():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    assert named_sndict_b.flatten(0).dim == named_sndict_b.dim
    assert named_sndict_b.flatten(1).dim == (3, 5)
    assert list_equal(
        map(tuple, named_sndict_b.flatten(1).keys()),
        [('key1', 'key1_1'), ('key2', 'key2_1'), ('key2', 'key2_2')],
    )
    assert named_sndict_b.flatten(1).level_names == ("a___b", "c")
    assert_raises(LevelError, named_sndict_b.flatten, 3)


def test_stratify():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    flattened_stratified_named_sndict_b = named_sndict_b\
        .flatten(1, named=True).stratify(1)
    assert list_equal(
        flattened_stratified_named_sndict_b.level_names,
        ["a", "b", "c"]
    )
    assert flattened_stratified_named_sndict_b.dim == (2, 3, 5)
    assert flattened_stratified_named_sndict_b


def test_str():
    assert strip_spaces(str(StructuredNestedDict(dict_b, levels=2))) == \
        "StructuredNestedDict({'key1':{'key1_1':{'key1_1_1':'val1_1_1'," \
        "'key1_1_2':'val1_1_2',},},'key2':{'key2_1':{'key2_1_1':'val2_1_1'," \
        "'key2_1_2':'val2_1_2',},'key2_2':{'key2_2_1':'val2_2_1',},}," \
        "'key3':{},},levels=2)"

    assert strip_spaces(str(
        StructuredNestedDict(dict_b, levels=2, level_names=["a", "b"])
    )) == "StructuredNestedDict({'key1':{'key1_1':{'key1_1_1':'val1_1_1'," \
          "'key1_1_2':'val1_1_2',},},'key2':{'key2_1':{'key2_1_1':'val2_1_1'," \
          "'key2_1_2':'val2_1_2',},'key2_2':{'key2_2_1':'val2_2_1',},}," \
          "'key3':{},},levels=2,level_names=('a','b'))"


def test_filter_key():
    sndict_b = StructuredNestedDict(dict_b, levels=3)
    assert list_equal(
        sndict_b.filter_key(["key1"]).keys(),
        ['key1']
    )
    assert list_equal(
        sndict_b.filter_key([["key1", "key3"]]).keys(),
        ['key1', 'key3'],
    )
    assert list_equal(
        sndict_b.filter_key([["key1", "key3"]], drop_empty=True).keys(),
        ['key1'],
    )
    assert list_equal(
        sndict_b.filter_key([slice(None), "key1_1"]).flatten_values(),
        ['val1_1_1', 'val1_1_2'],
    )


def test_filter_funcs():
    assert _get_filter_func(slice(None))(False)
    assert _get_filter_func(slice(None))(True)
    assert _get_filter_func(lambda i: i % 2 == 0)(2)
    assert not _get_filter_func(lambda i: i % 2 == 0)(1)
    assert _get_filter_func([1, 2, 3])(1)
    assert not _get_filter_func([1, 2, 3])(4)
    assert _get_filter_func(1)(1)
    assert not _get_filter_func(slice(None), filter_out=True)(True)


def test_rename_levels():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])

    named_sndict_b2 = named_sndict_b.modify_metadata(levels=2)
    assert named_sndict_b2.levels == 2
    assert_raises(LevelError, named_sndict_b2.flatten, 2)

    named_sndict_b2 = named_sndict_b.modify_metadata(
        levels=3, level_names=["A", "B", "C"])
    assert named_sndict_b2.level_names == ("A", "B", "C")


def test_rearrange():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    assert list_equal(
        named_sndict_b.rearrange([1, 0]).flatten_keys(2, named=False),
        [('key1_1', 'key1', 'key1_1_1'),
         ('key1_1', 'key1', 'key1_1_2'),
         ('key2_1', 'key2', 'key2_1_1'),
         ('key2_1', 'key2', 'key2_1_2'),
         ('key2_2', 'key2', 'key2_2_1')],
    )
    assert named_sndict_b.rearrange([1, 0]).level_names \
        == ("b", "a", "c")
    assert named_sndict_b.rearrange([0, 1]).level_names \
        == ("a", "b", "c")

    assert list_equal(
        named_sndict_b\
            .rearrange(["c", "b", "a"])\
            .flatten_keys(2, named=False),
        [('key1_1_1', 'key1_1', 'key1'),
         ('key1_1_2', 'key1_1', 'key1'),
         ('key2_1_1', 'key2_1', 'key2'),
         ('key2_1_2', 'key2_1', 'key2'),
         ('key2_2_1', 'key2_2', 'key2')],
    )
    assert named_sndict_b.rearrange(["c", "b", "a"]).level_names \
        == ("c", "b", "a")


def test_swap_levels():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    assert named_sndict_b.swap_levels("c", "a").level_names == \
        ("c", "b", "a")


def test__delitem__():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    del named_sndict_b["key2"]
    assert list_equal(
        named_sndict_b.flatten_values(),
        ['val1_1_1', 'val1_1_2'],
    )
    assert named_sndict_b.dim == (2, 1, 2)


def test__setitem__():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    named_sndict_b["newkey"] = {}
    assert named_sndict_b.dim == (4, 3, 5)
    assert named_sndict_b["newkey"].levels == 2
    assert named_sndict_b["newkey"].level_names == ("b", "c")

    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    try:
        named_sndict_b["newkey"] = {1: 1}
        raise Exception
    except TypeError:
        pass

    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    named_sndict_b["newkey"] = {1: {2: 3, 4: 5}}
    assert named_sndict_b.dim == (4, 4, 7)
    assert named_sndict_b["newkey"].levels == 2
    assert named_sndict_b["newkey"].level_names == ("b", "c")


def test_sort_keys():
    named_sndict_b = StructuredNestedDict(
        dict_b, levels=3, level_names=["a", "b", "c"])
    assert list_equal(
        named_sndict_b.sort_keys(reverse=True).keys(),
        ['key3', 'key2', 'key1'],
    )


def test_sort_values():
    assert list_equal(
        StructuredNestedDict({"a": "z", "b": "y", "c": "x"})
            .sort_values().values(),
        ["x", "y", "z"],
    )


def test_nested_set_and_get():
    sndict = StructuredNestedDict(dict_b, levels=3)
    assert sndict.has_nested_key(('key1', 'key1_1', 'key1_1_1'))
    assert not sndict.has_nested_key(('keyX', 'keyX_1', 'keyX_1_1'))

    sndict.nested_set(('keyX', 'keyX_1', 'keyX_1_1'), "valX_1_1")
    assert sndict.has_nested_key(('keyX', 'keyX_1', 'keyX_1_1'))
    assert sndict.nested_get(('keyX', 'keyX_1', 'keyX_1_1')) == "valX_1_1"


def test_ix():
    sndict = StructuredNestedDict(dict_b, levels=3)
    assert sndict.ix['key1', 'key1_1', 'key1_1_1'] == "val1_1_1"
    try:
        _ = sndict.ix['keyX', 'keyX_1', 'keyX_1_1']
        raise RuntimeError
    except KeyError:
        pass

        sndict.ix['keyX', 'keyX_1', 'keyX_1_1'] = "valX_1_1"
    assert sndict.ix['keyX', 'keyX_1', 'keyX_1_1'] == "valX_1_1"
