import collections as col
import types

from utils import replace_none, identity
from exceptions import LevelError


class _NothingClass(object):
    """Non-informative class for expressing "default" values, that isn't None"""
    pass

_NOTHING = _NothingClass()


class XDict(col.OrderedDict):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        if args and isinstance(args[0], XDict) and not args[0]._dim is None:
            self._dim = args[0]._dim
        else:
            self._dim = None

    @property
    def dim(self):
        """The dimensions of the XDict, express as a tuple of the widths of each
        level.

        Because this is a relatively heavy operation, we want to aggressively
        cache this.

        Returns
        -------
        tuple
        """
        if self._dim is None:
            dimension_dict = col.defaultdict(lambda: 0)

            def _dfs(obj, depth):
                dimension_dict[depth] += 1
                if depth > 1 and isinstance(obj, XDict):
                    for obj_depth, obj_width in enumerate(obj.dim, start=depth+1):
                        dimension_dict[obj_depth] += obj_width
                elif isinstance(obj, dict):
                    if depth + 1 not in dimension_dict:
                        dimension_dict[depth + 1] = 0
                    for _, val in obj.iteritems():
                        _dfs(val, depth + 1)

            _dfs(self, depth=0)

            self._dim = tuple([
                dimension_dict[level]
                for level in range(1, len(dimension_dict))
            ])

        return self._dim

    @property
    def levels(self):
        """Number of levels (depth) of the XDict

        Returns
        -------
        int
        """
        return len(self.dim)

    @property
    def flat_len(self):
        """Width of lowest (deepest) level of XDict

        Returns
        -------
        int
        """
        return self.dim[-1]

    def deepcopy(self):
        """Recursively copy XDict and nested dictionaries. Note that this does
        not deepcopy non-dict objects

        Returns
        -------
        XDict
        """
        def _recursive_copy(dictionary):
            return dictionary.__class__([
                (key, _recursive_copy(val) if isinstance(val, dict) else val)
                for key, val in dictionary.iteritems()
            ])

        return _recursive_copy(self)

    def flatten(self, levels=None):
        """Flatten an XDict a number of levels, starting from the top

        .flatten(0) => Flatten 0 layers => No change
        .flatten(1) => Flatten 1 layer => Returned XDict is one level shorter

        WARNING: Flattening will lose information about empty dicts that aren't
        at the lowest level. This is because empty dicts will not be represented
        in the resultant flattened dict

        Parameters
        ----------
        levels: int, optional
            Number of levels to flatten by. If not supplied, all levels are
            flattened (i.e. flattened to a 1-layer deep dict)

        Returns
        -------
        XDict:
            Flattened XDict, with fewer or equal number of levels
        """

        levels = replace_none(levels, self.levels-1)
        levels = self._wrap_negative_level(levels)
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
        """Nest dictionaries by breaking up top-level key-tuples into levels
        E.g. Going from
            {(1, 2, 3): 4}
        To
            {1: {2: {3:, 4}}

        Parameters
        ----------
        levels: int, optional
            Number of levels to stratify XDict by. If not supplied, levels
            is inferred from top-level tuple.

        Returns
        -------
        XDict
            Stratified XDict, with greater or equal number of levels
        """
        if levels == 0 or len(self) == 0:
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
        """Flatten at a given level

        Parameters
        ----------
        level: int
            Level to apply flatten at
        levels: int, optional.
            Number of levels of flatten. See: XDict.flatten

        Returns
        -------
        XDict
            XDict flattened at some level
        """
        if level == 0:
            return self.flatten(levels)
        return self.val_map(
            lambda inner_dict: self.__class__(inner_dict).flatten(levels),
            level=level-1,
        )

    def stratify_at(self, level, levels=None):
        """Stratify at a given level

        Parameters
        ----------
        level: int
            Level to apply stratify at
        levels: int, optional.
            Number of levels of stratify. See: XDict.stratify

        Returns
        -------
        XDict
            XDict stratified at some level
        """
        if level == 0:
            return self.stratify(levels)
        return self.val_map(
            lambda inner_dict: self.__class__(inner_dict).stratify(levels),
            level=level-1,
        )

    def key_map(self, key_func, level=0):
        """Transform keys of XDict. Resultant keys must be unique within the
        same dictionary

        Parameters
        ----------
        key_func: callable
            Function to apply to keys
        level: int, optional
            Level at which to apply key-transformations to.

        Returns
        -------
        XDict:
            XDict with transformed keys
        """
        return self._generic_map(key_func=key_func, level=level)

    def val_map(self, val_func, level=0):
        """Transform values of XDict.

        Parameters
        ----------
        val_func: callable
            Function to apply to values
        level: int, optional
            Level at which to apply value-transformations to.

        Returns
        -------
        XDict:
            XDict with transformed keys
        """
        return self._generic_map(val_func=val_func, level=level)

    def _generic_map(self, key_func=None, val_func=None, level=0):
        """Generic method for simultaneously applying key- and value-
        transformations at a given level

        Parameters
        ----------
        key_func: callable
            Function to apply to keys
        val_func: callable
            Function to apply to values
        level: int, optional
            Level at which to apply transformations to.

        Returns
        -------
        XDict:
            XDict with transformed keys/values
        """
        # 0-indexed
        level = self._wrap_negative_level(level)
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
        """Generic method for simultaneously applying key- and value-
        transformations for a simple dict.

        Parameters
        ----------
        key_func: callable
            Function to apply to keys
        val_func: callable
            Function to apply to values

        Returns
        -------
        XDict:
            XDict with tranfsormed keys/values
        """
        # 0-indexed
        key_func = replace_none(key_func, identity)
        val_func = replace_none(val_func, identity)
        new_dict = self.__class__([
            (key_func(key), val_func(val))
            for key, val in self.iteritems()
        ])
        assert len(new_dict) == len(self)
        return new_dict

    def filter_key(self, key_filter, filter_in=True, level=0):
        if level == 0:
            return self._generic_filter(
                key_filter=key_filter, filter_in=filter_in,
            )
        else:
            return self.val_map(lambda _: self.__class__(_).filter_key(
                key_filter=key_filter, filter_in=filter_in,
            ), level=level)

    def filter_val(self, val_filter, filter_in=True, level=0):
        if level == 0:
            return self._generic_filter(
                val_filter=val_filter, filter_in=filter_in,
            )
        else:
            return self.val_map(lambda _: self.__class__(_).filter_val(
                val_filter=val_filter, filter_in=filter_in,
            ), level=level)

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

    def subset(self, key_ls):
        return self.__class__([
            (key, self[key])
            for key in key_ls
        ])

    def set_chain(self, key_ls, val, inplace=True):

        if not inplace:
            new_dict = self.deepcopy()
            new_dict.set_chain(key_ls=key_ls, val=val, inplace=True)
            return new_dict

        if isinstance(val, dict):
            if not len(key_ls) + XDict(val).levels == self.levels:
                raise LevelError(
                    "key_ls depth + val depth ({}, {}) does not match levels "
                    "({})".format(len(key_ls), XDict(val).levels, self.levels))
        else:
            if not len(key_ls) == self.levels:
                raise LevelError("key_ls depth ({}) does not match levels "
                                 "({})".format(len(key_ls), self.levels))

        pointer = self
        for key in key_ls[:-1]:
            if key not in pointer:
                pointer[key] = self.__class__()
            pointer = pointer[key]

        if key_ls[-1] not in pointer:
            new_dim = list(self._dim)
            new_dim[len(key_ls) - 1] += 1
            self._dim = new_dim

        pointer[key_ls[-1]] = val

    def get_chain(self, key_ls, default=_NOTHING):
        if not key_ls:
            raise LevelError("Cannot get_chain with empty key_ls")

        pointer = self
        try:
            for key in key_ls:
                pointer = pointer[key]

            # TYPEHACK
            if isinstance(pointer, dict):
                pointer = self.__class__(pointer)
            return pointer
        except KeyError:
            if isinstance(default, _NothingClass):
                raise KeyError(key_ls)
            else:
                return default

    def convert(self, mode=None):
        if mode in [dict, col.OrderedDict, XDict]:
            dict_class = mode
        elif mode is None or mode == "xdict":
            dict_class = self.__class__
        elif mode == "dict":
            dict_class = dict
        elif mode == "odict":
            dict_class = col.OrderedDict
        else:
            raise KeyError(mode)

        return dict_class([
            (key, XDict(val).convert(mode) if isinstance(val, dict) else val)
            for key, val in self.iteritems()
        ])

    def to_dict(self):
        return self.convert("dict")

    def to_odict(self):
        return self.convert("odict")

    def to_xdict(self):
        return self.convert("xdict")

    def sort_key(self, by=None, reverse=False):
        by = replace_none(by, identity)
        return self.__class__(sorted(
            self.items(), key=lambda _: by(_[0]), reverse=reverse
        ))

    def sort_val(self, by=None, reverse=False):
        by = replace_none(by, identity)
        return self.__class__(sorted(
            self.items(), key=lambda _: by(_[1]), reverse=reverse
        ))

    def _wrap_negative_level(self, level):
        return _wrap_negative_level(level, total_levels=self.levels)

    def reorder_levels(self, level_ls):
        if set(level_ls) != set(range(min(len(level_ls), self.levels)))\
                or len(level_ls) - 1 != max(level_ls):
            raise LevelError("Improper level_ls {} supplied.".format(level_ls))

        max_level = max(level_ls)
        new_dict = XDict()
        for flattened_key, val in self.flatten(levels=max_level).iteritems():
            new_key = tuple(flattened_key[i] for i in level_ls)
            new_dict[new_key] = val
        return new_dict.stratify(max_level)

    def swap_levels(self, level_a, level_b):
        if level_a == level_b\
                or level_a > self.levels\
                or level_b > self.levels:
            raise LevelError("Improper levels to swap: ({}, {})".format(
                level_a, level_b,
            ))
        level_ls = range(max(level_a, level_b) + 1)
        level_ls[level_a], level_ls[level_b] = level_b, level_a
        return self.reorder_levels(level_ls)


def _wrap_negative_level(level, total_levels):
    if level >= 0:
        return level
    else:
        wrapped_level = total_levels + level
        assert wrapped_level >= 0
        return wrapped_level
