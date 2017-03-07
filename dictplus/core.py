import collections as col
import types

from utils import replace_none
from exceptions import LevelError


class XDict(col.OrderedDict):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self._levels = None

    @property
    def levels(self):
        if self._levels is None:
            current = self
            levels = 0
            while isinstance(current, dict):
                levels += 1
                if not current:
                    break
                current = current.values()[0]
            self._levels = levels
        return self._levels

    @property
    def flat_len(self):
        return len(self.flatten())

    def deepcopy(self):
        def _recursive_copy(dictionary):
            return dictionary.__class__([
                (key, _recursive_copy(val) if isinstance(val, dict) else val)
                for key, val in dictionary.iteritems()
            ])

        return _recursive_copy(self)

    def flatten(self, levels=None):
        levels = replace_none(levels, self.levels-1)
        levels = _wrap_negative_level(levels, total_levels=self.levels)
        if levels >= self.levels:
            raise LevelError(
                "Trying to flatten too many levels ({}) in a {}-level "
                "XDict".format(levels, self.levels))
        elif levels == 0:
            return self.copy()

        new_dict_as_list = list()

        def _accumulate_keys(data, partial_key, levels_remaining):
            if levels_remaining == 0:
                new_dict_as_list.append((tuple(partial_key), data))
            else:
                assert isinstance(data, dict), \
                    "Failed to flatten at level={}. " \
                    "Did we flatten too far, or is the dictionary " \
                    "malformed?".format(levels - levels_remaining + 1)

                for sub_key, val in data.iteritems():
                    _accumulate_keys(
                        data=val,
                        partial_key=partial_key + [sub_key],
                        levels_remaining=levels_remaining - 1
                    )

        _accumulate_keys(self, [], levels + 1)

        return self.__class__(new_dict_as_list)

    def stratify(self, levels=None):
        if levels == 0:
            return self.copy()

        if not self:
            return self.__class__()

        sample_key = self.keys()[0]
        assert isinstance(sample_key, tuple)
        levels = replace_none(levels, len(sample_key)-1)
        levels = _wrap_negative_level(levels, total_levels=len(sample_key))
        if levels >= len(sample_key):
            raise LevelError("Trying to stratify too many levels ({}) from "
                             "a level-{} key".format(levels, len(sample_key)))

        new_dict = self.__class__()
        for key, val in self.iteritems():
            curr_dict = new_dict
            for sub_key in key[:levels]:
                if sub_key not in curr_dict:
                    curr_dict[sub_key] = self.__class__()
                curr_dict = curr_dict[sub_key]

            remaining_key = key[levels:]
            if len(remaining_key) == 1:
                curr_dict[remaining_key[0]] = val
            else:
                curr_dict[remaining_key] = val
        return new_dict

    def flatten_at(self, level, levels=None):
        if level == 0:
            return self.flatten(levels)
        return self.val_map(
            lambda inner_dict: self.__class__(inner_dict).flatten(levels),
            level=level-1,
        )

    def stratify_at(self, level, levels=None):
        if level == 0:
            return self.stratify(levels)
        return self.val_map(
            lambda inner_dict: self.__class__(inner_dict).stratify(levels),
            level=level-1,
        )

    def _generic_map(self, key_func=None, val_func=None, level=0):
        # 0-indexed
        level = _wrap_negative_level(level, total_levels=self.levels)
        key_func = replace_none(key_func, identity)
        val_func = replace_none(val_func, identity)
        assert level < self.levels

        if level == 0:
            return self._simple_generic_map(
                key_func=key_func, val_func=val_func
            )
        else:
            return self.flatten(level-1)\
                ._simple_generic_map(
                    val_func=lambda inner_dict: self.__class__(inner_dict)
                        ._simple_generic_map(key_func=key_func,
                                             val_func=val_func,))\
                .stratify(level-1)

    def _simple_generic_map(self, key_func=None, val_func=None):
        # 0-indexed
        key_func = replace_none(key_func, identity)
        val_func = replace_none(val_func, identity)
        new_dict = self.__class__([
            (key_func(key), val_func(val))
            for key, val in self.iteritems()
        ])
        assert len(new_dict) == len(self)
        return new_dict

    def key_map(self, key_func, level=0):
        return self._generic_map(key_func=key_func, level=level)

    def val_map(self, val_func, level=0):
        return self._generic_map(val_func=val_func, level=level)

    def chain_ix(self, key_ls):
        curr_pointer = self
        for key in key_ls:
            curr_pointer = curr_pointer[key]

        # TYPEHACK
        if isinstance(curr_pointer, dict):
            curr_pointer = self.__class__(curr_pointer)

        return curr_pointer

    """
    def chain_ix_at(self, key_ls, level=0):
        if level == 0:
            return self.chain_ix(key_ls)
        return self.val_map(
            lambda inner_dict: self.__class__(inner_dict).chain_ix_at(key_ls),
            level=level-1,
        )
    """

    def _generic_filter(self, key_filter=None, val_filter=None, filter_in=True):

        def _get_filter_func(val_or_ls_or_lambda):
            if val_or_ls_or_lambda is None:
                filter_func = lambda x: True
            elif isinstance(val_or_ls_or_lambda, types.FunctionType):
                filter_func = val_or_ls_or_lambda
            elif isinstance(val_or_ls_or_lambda, list):
                filter_func = lambda x: x in val_or_ls_or_lambda
            else:
                filter_func = lambda x: x == val_or_ls_or_lambda

            if not filter_in:
                filter_func = lambda x: not x

            return filter_func

        key_filter_func = _get_filter_func(key_filter)
        val_filter_func = _get_filter_func(val_filter)

        return self.__class__([
            (key, val)
            for key, val in self.iteritems()
            if key_filter_func(key) and val_filter_func(val)
        ])

    def filter_key(self, key_filter, filter_in=True):
        return self._generic_filter(key_filter=key_filter, filter_in=filter_in)

    def filter_val(self, val_filter, filter_in=True):
        return self._generic_filter(val_filter=val_filter, filter_in=filter_in)


def identity(x):
    return x


def _wrap_negative_level(level, total_levels):
    if level >= 0:
        return level
    else:
        wrapped_level = total_levels + level
        assert wrapped_level >= 0
        return wrapped_level

