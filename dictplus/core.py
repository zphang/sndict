import collections as col
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

    def deepcopy(self):
        def _recursive_copy(dictionary):
            return dictionary.__class__([
                (key, _recursive_copy(val) if isinstance(val, dict) else val)
                for key, val in dictionary.iteritems()
            ])

        return _recursive_copy(self)

    def flatten(self, levels=None):
        levels = replace_none(levels, self.levels-1)
        levels = _wrap_negative_level(levels, tota  l_levels=self.levels)
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

    def ix(self, key_ls):
        if len(key_ls) == self.levels:
            dict_to_index = self
        else:
            dict_to_index = self.flatten(levels)


def identity(x):
    return x


def _wrap_negative_level(level, total_levels):
    if level >= 0:
        return level
    else:
        wrapped_level = total_levels + level
        assert wrapped_level >= 0
        return wrapped_level

