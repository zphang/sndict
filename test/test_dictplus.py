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


def test_levels():
    assert XDict({0: 1}).levels == 1
    assert XDict({0: {1: 2}}).levels == 2
    assert XDict({0: {1: 2}}).levels == 2
    assert XDict({0: {}}).levels == 2
    assert XDict({0: XDict()}).levels == 2

    assert XDict(dict_a).levels == 2
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


def test_chain_ix():
    assert XDict(dict_b).chain_ix(["key1"]).levels == 2
    assert XDict(dict_b).chain_ix(["key1", "key1_1", "key1_1_1"]) == "val1_1_1"


def test_filter():
    assert XDict(dict_b).filter_key(["key1"]).flat_len == 2
    assert XDict(dict_b).filter_key(["key1", "key2"]).flat_len == 5
    assert XDict(dict_b).filter_key(lambda _: "key" in _).flat_len == 5
