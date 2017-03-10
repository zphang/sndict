import collections as col
from nose.tools import assert_raises

from dictplus.ndict import NDict
from dictplus.utils import list_equal


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
    assert NDict(dict_b, levels=1).dim == (3,)
    assert NDict(dict_b, levels=2).dim == (3, 3)
    assert NDict(dict_b, levels=3).dim == (3, 3, 5)


def test_iterflatten():
    ndict = NDict(dict_b, levels=3)
    assert list_equal(
        dict(ndict.iterflatten(1)).keys(),
        [('key1', 'key1_1'), ('key2', 'key2_2'), ('key2', 'key2_1')]
    )
    assert list_equal(
        dict(ndict.iterflatten(2)).values(),
        ['val1_1_2', 'val2_1_1', 'val2_1_2', 'val2_2_1', 'val1_1_1'],
    )
    assert_raises(RuntimeError, ndict.flatten, 5)
