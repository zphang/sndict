from sndict.shared import get_filter_func


def test_filter_funcs():
    assert get_filter_func(slice(None))(False)
    assert get_filter_func(slice(None))(True)
    assert get_filter_func(lambda i: i % 2 == 0)(2)
    assert not get_filter_func(lambda i: i % 2 == 0)(1)
    assert get_filter_func([1, 2, 3])(1)
    assert not get_filter_func([1, 2, 3])(4)
    assert get_filter_func(1)(1)
    assert not get_filter_func(slice(None), filter_out=True)(True)
