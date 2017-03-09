import collections as col
from dictplus.core import XDict
from dictplus.exceptions import LevelError
from nose.tools import assert_raises

dict_a = col.OrderedDict([
    ("key1", col.OrderedDict([
        ("key1_1", "val1_1"),
        ("key1_2", "val1_2"),
    ])),
    ("key2", col.OrderedDict([
        ("key2_1", "val1_1"),
        ("key2_2", "val1_2"),
        ("key2_3", "val1_3"),
    ])),
    ("key3", col.OrderedDict()),
])

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

empty_dict = dict()


def test_dim():
    assert XDict({0: 1}).dim == (1,)
    assert XDict({0: {1: 2}}).dim == (1, 1)
    assert XDict({0: {}}).dim == (1, 0)
    assert XDict({0: XDict()}).dim == (1, 0)

    assert XDict(dict_a).dim == (3, 5)
    assert XDict(dict_b).dim == (3, 3, 5)
    assert XDict(empty_dict).dim == (0,)


def test_levels():
    assert XDict({0: 1}).levels == 1
    assert XDict({0: {1: 2}}).levels == 2
    assert XDict({0: {}}).levels == 2
    assert XDict({0: XDict()}).levels == 2

    assert XDict(dict_a).levels == 2
    assert XDict(dict_b).levels == 3
    assert XDict(empty_dict).levels == 1


def test_flat_len():
    assert XDict(dict_b).flat_len == 5


def test_flatten():
    assert XDict(dict_a).flatten(1) == XDict(dict_a).flatten()
    flattened_dict_a = XDict(dict_a).flatten(1)
    assert flattened_dict_a.levels == XDict(dict_a).levels - 1
    assert len(flattened_dict_a) == 5
    assert flattened_dict_a.keys()[0] == ("key1", "key1_1")
    assert flattened_dict_a.values()[0] == "val1_1"

    assert XDict(dict_a).flatten(0).levels == XDict(dict_a).levels
    assert XDict(dict_a).flatten(-1).levels == XDict(dict_a).levels - 1
    assert XDict(dict_a).flatten(-2).levels == XDict(dict_a).levels


def test_bad_flatten():
    assert_raises(LevelError, XDict(dict_a).flatten, 3)
    assert_raises(LevelError, XDict(dict_a).flatten, 2)
    assert_raises(LevelError, XDict(empty_dict).flatten, 1)


def test_stratify():
    flattened_dict_b = XDict(dict_b).flatten()

    assert XDict(flattened_dict_b).stratify(0).levels == flattened_dict_b.levels
    assert XDict(flattened_dict_b).stratify().levels == \
        XDict(flattened_dict_b).stratify(2).levels
    assert XDict(flattened_dict_b).stratify(-1).levels == \
        XDict(flattened_dict_b).stratify(2).levels

    stratified_dict_b_lv1 = XDict(flattened_dict_b).stratify(1)
    assert stratified_dict_b_lv1.levels == 2
    assert stratified_dict_b_lv1.keys()[0] == "key1"
    assert len(stratified_dict_b_lv1) == 2
    assert stratified_dict_b_lv1.values()[0].keys()[0] == ("key1_1", "key1_1_1")
    assert stratified_dict_b_lv1.values()[0].values()[0] == "val1_1_1"

    stratified_dict_b_lv2 = XDict(flattened_dict_b).stratify(2)
    assert stratified_dict_b_lv2.levels == 3
    assert stratified_dict_b_lv2.keys()[0] == "key1"
    assert len(stratified_dict_b_lv2) == 2
    assert stratified_dict_b_lv2.values()[0].keys()[0] == "key1_1"
    assert stratified_dict_b_lv2.values()[0].values()[0].keys()[0] == \
        "key1_1_1"
    assert stratified_dict_b_lv2.values()[0].values()[0].values()[0] == \
        "val1_1_1"

    assert XDict(empty_dict).stratify(10).levels == 1


def test_flatten_at():
    assert XDict(dict_b).flatten_at(1).keys()[0] == "key1"
    assert XDict(dict_b).flatten_at(1).values()[0].keys()[0] == ("key1_1", "key1_1_1")


def test_stratify_at():
    assert XDict(dict_b).flatten_at(1).stratify_at(1).levels == 3


def test_bad_stratify():
    flattened_dict_b = XDict(dict_a).flatten()
    assert_raises(LevelError, flattened_dict_b.stratify, 3)


def test_key_map():
    assert XDict(dict_b).key_map(str.upper).keys()[0] == "KEY1"
    assert XDict(dict_b).key_map(str.upper, level=1).values()[0]\
        .keys()[0] == "KEY1_1"


def test_val_map():
    assert XDict(dict_b).val_map(len).values()[0] == 1
    assert XDict(dict_b).val_map(len, level=1).keys()[0] == "key1"
    assert XDict(dict_b).val_map(len, level=1)\
        .values()[0].keys()[0] == "key1_1"
    assert XDict(dict_b).val_map(len, level=1)\
        .values()[0].values()[0] == 2


def test_empty_sub_dict_is_dropped():
    assert "key3" in XDict(dict_b)
    assert "key3" not in XDict(dict_b).flatten().stratify()


def test_filter():
    assert XDict(dict_b).filter_key(["key1"]).flat_len == 2
    assert XDict(dict_b).filter_key(["key1", "key2"]).flat_len == 5
    assert XDict(dict_b).filter_key(lambda _: "key" in _).flat_len == 5

    assert XDict(dict_b).filter_key(lambda _: "key" in _).flat_len == 5


def test_subset():
    subset_dict = XDict(dict_b).subset(["key2", "key1"])
    assert len(subset_dict) == 2
    assert subset_dict.keys()[0] == "key2"
    assert subset_dict.keys()[1] == "key1"


def test_get_chain():
    assert XDict(dict_b).get_chain(["key1"]).levels == 2
    assert XDict(dict_b).get_chain(["key1", "key1_1", "key1_1_1"]) == "val1_1_1"
    assert XDict(dict_b).get_chain(["key100"], 1234) == 1234
    assert_raises(KeyError, XDict(dict_b).get_chain, ["key100"])


def test_set_chain():
    sample_dict = XDict(dict_b)
    assert_raises(LevelError, sample_dict.set_chain, range(10), "val")
    sample_dict.set_chain(range(3), "val")
    assert sample_dict[0][1][2] == "val"

    sample_dict = XDict(dict_b)
    new_dict = sample_dict.set_chain(range(3), "val", inplace=False)
    assert sample_dict.flat_len == 5
    assert new_dict.flat_len == 6


def test_convert():
    converted_b = XDict(dict_b).convert()
    assert isinstance(converted_b, XDict)
    assert isinstance(converted_b.values()[0], XDict)
    assert isinstance(converted_b.values()[0].values()[0], XDict)

    converted_b = XDict(dict_b).convert("odict")
    assert isinstance(converted_b, col.OrderedDict)
    assert isinstance(converted_b.values()[0], col.OrderedDict)
    assert isinstance(converted_b.values()[0].values()[0], col.OrderedDict)

    assert isinstance(XDict(empty_dict).convert(), XDict)


def test_sort():
    new_dict = XDict([
        (9, 8),
        (0, 9),
        (1, 2),
        (4, 7),
        (7, 3),
        (3, 6),
        (6, 4),
        (8, 5),
        (5, 1),
        (2, 0),
    ])
    assert tuple(new_dict.sort_key().keys()) == tuple(range(10))
    assert tuple(new_dict.sort_val().values()) == tuple(range(10))
    assert tuple(new_dict.sort_key(lambda x: -x).keys()) == tuple(range(10)[::-1])
    assert tuple(new_dict.sort_val(lambda x: -x).values()) == tuple(range(10)[::-1])
    assert tuple(new_dict.sort_key(reverse=True).keys()) == tuple(range(10)[::-1])
    assert tuple(new_dict.sort_val(reverse=True).values()) == tuple(range(10)[::-1])


def test_reorder_levels():
    assert tuple(XDict(dict_a).reorder_levels([1, 0]).keys()) == \
        ("key1_1", "key1_2", "key2_1", "key2_2", "key2_3")
    assert tuple(XDict(dict_b).reorder_levels([2, 1, 0]).keys()) == \
        ("key1_1_1", "key1_1_2", "key2_1_1", "key2_1_2", "key2_2_1")
    assert tuple(XDict(dict_b).reorder_levels([2, 1, 0]).keys()) == \
        ("key1_1_1", "key1_1_2", "key2_1_1", "key2_1_2", "key2_2_1")
    assert tuple(XDict(dict_b).reorder_levels([2, 1, 0]).values()[0].keys()) ==\
        ("key1_1",)


def test_swap_levels():
    assert XDict(dict_b).swap_levels(1, 2).get_chain([
        "key2", "key2_2_1", "key2_2"
    ]) == "val2_2_1"
