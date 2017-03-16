import collections as col
import types

from nesteddict import NestedDict
from exceptions import LevelError
from utils import (
    GetSetFunctionClass, GetSetAmbiguousTupleFunctionClass,
    list_add, list_index, list_is_unique,
    tuple_constructor,
    dict_to_string, get_str_func,
    replace_none, identity, negate,
)

FLATTENED_LEVEL_NAME_SEPARATOR = "___"


class StructuredNestedDict(col.OrderedDict):

    def __init__(self, *args, **kwargs):
        """Extension of OrderedDict that exposes advanced operations on nested
        dicts of fixed depth

        Parameters
        ----------
        data: dict, or list
            Nested dictionary
        levels: int
            Number of levels
        level_names: list
            List of level names
        """
        # Extract kwargs
        level_names = kwargs.pop("level_names", None)
        if level_names is None:
            levels = kwargs.pop("levels", 1)
        else:
            levels = kwargs.pop("levels", len(level_names))

        self._nested_initialized = False

        # Custom initialization
        self._levels = levels
        if level_names is None:
            self._level_names_is_set = False
            self._level_names = None  # Lazily initialize
        else:
            assert len(level_names) == self._levels
            assert list_is_unique(level_names)
            self._level_names_is_set = True
            self._level_names = level_names

        # Initialize superclass
        super(self.__class__, self).__init__(*args, **kwargs)

    @classmethod
    def groupby(cls, data, by, levels=None, level_names=None):
        """Initialize by grouping elements from list

        Parameters
        ----------
        data: list or dictionary
            List or dictionary to group by
        by: function
            Function applied to list elements to form key elements
        levels: int
            Number of levels
        level_names: list
            List of level names

        Returns
        -------
        StructuredNestedDict
        """
        new_dict = col.OrderedDict()
        if isinstance(data, dict):
            for key, val in data.iteritems():
                new_dict[by(key)] = val
        else:
            for elem in data:
                new_dict[by(elem)] = elem
        new_sndict = StructuredNestedDict(new_dict)

        if levels is None and level_names is None:
            return new_sndict
        elif levels is not None and level_names is None:
            return new_sndict.stratify(levels=levels-1)
        elif levels is None and level_names is not None:
            levels = len(level_names)
            return new_sndict.stratify(levels=levels-1) \
                .replace_metadata(level_names=level_names)
        else:
            raise RuntimeError("Don't supply both levels and level_names")

    # ==== Properties ==== #

    @property
    def dim(self):
        """Dimensions of whole StructuredNestedDict, up to defined level

        Returns
        -------
        tuple:
            Tuple of widths of nested dictionaries, one per level
        """
        if self.levels == 1:
            return len(self),
        dim_list = [[0] * (self._levels - 1)]
        for sub_dict in self.values():
            dim_list.append(sub_dict.dim)
        return (len(self),) + tuple(list_add(dim_list))

    @property
    def levels(self):
        """Number of levels

        Returns
        -------
        int
        """
        return self._levels

    @property
    def level_names(self):
        """Names of levels. Defaults to ["level0", "level1", ...] is no names
        are provided

        Returns
        -------
        list
        """
        if self._level_names_is_set:
            return tuple(self._level_names)
        else:
            return ["level{i}".format(i=i) for i in xrange(self._levels)]

    @property
    def dim_dict(self):
        """Dimensions of whole StructuredNestedDict as dict, up to defined level

        Returns
        -------
        dict
            Dimensions keyed by level name
        """
        return dict(zip(self.level_names, self._dim))

    # ==== Iterators ==== #

    def iterflatten(self, levels=1, named=True):
        """Returns an iterator with multiple levels flattened

        WARNING:
            If there are empty dictionaries within the levels being flattened,
            their keys will be lost. This is consistent with the logic of
            flattening - those dictionaries contain no values for a
            (level-tuple)-keyed dictionary.

        Note:
            .flatten(levels=0) does nothing,
            .flatten(levels=1) compresses 1 level (i.e. keys will be 2-ples)

        Parameters
        ----------
        levels: int, default=1
            Number of levels to flatten by.
            Defaults to flattening one level
        named: bool
            Whether output key-tuples are namedtuples

        Returns
        -------
        StructuredNestedDict
        """
        levels = self._wrap_level(levels)
        if levels is None:
            levels = self.levels - 1
        else:
            levels = self._wrap_level(levels)

        if named:
            key_tup_class = self.get_named_tuple(levels=levels + 1)
        else:
            key_tup_class = tuple_constructor
        for key_ls, val in self._iterflatten(levels=levels):
            yield key_tup_class(*key_ls), val

    def _iterflatten(self, levels):
        """Underlying iterator for flattening"""
        levels = self._wrap_level(levels)

        # flatten 0 = nothing, flatten 1 = 1
        for key, val in self.iteritems():
            # TODO: stop levels from being too deep
            if levels > 0:
                if not isinstance(val, StructuredNestedDict):
                    raise LevelError()
                for partial_key_tup, sub_val in val._iterflatten(levels - 1):
                    yield (key,) + partial_key_tup, sub_val
            else:
                yield (key,), val

    def iterflatten_keys(self, levels=1, named=True):
        """Returns an iterator with of keys of flattened dict

        WARNING:
            If there are empty dictionaries within the levels being flattened,
            their keys will be lost. This is consistent with the logic of
            flattening - those dictionaries contain no values for a
            (level-tuple)-keyed dictionary.

        Note:
            .flatten(levels=0) does nothing,
            .flatten(levels=1) compresses 1 level (i.e. keys will be 2-ples)

        Parameters
        ----------
        levels: int, default=1
            Number of levels to flatten by.
            Defaults to flattening one level
        named: bool
            Whether output key-tuples are namedtuples

        Returns
        -------
        list
        """
        levels = self._wrap_level(levels)
        for key, _ in self.iterflatten(levels=levels, named=named):
            yield key

    def iterflatten_values(self, levels=-1):
        """Returns an iterator with of values of flattened dict

        WARNING:
            If there are empty dictionaries within the levels being flattened,
            their keys will be lost. This is consistent with the logic of
            flattening - those dictionaries contain no values for a
            (level-tuple)-keyed dictionary.

        Note:
            .flatten(levels=0) does nothing,
            .flatten(levels=1) compresses 1 level (i.e. keys will be 2-ples)

        Parameters
        ----------
        levels: int, default=-1
            Number of levels to flatten by.
            Defaults to flattening all levels.

        Returns
        -------
        list
        """
        levels = self._wrap_level(levels)
        for _, values in self.iterflatten(levels=levels, named=False):
            yield values

    def flatten(self, levels=1, named=True, flattened_name=None):
        """Returns an StructuredNestedDict with multiple levels flattened

        WARNING:
            If there are empty dictionaries within the levels being flattened,
            their keys will be lost. This is consistent with the logic of
            flattening - those dictionaries contain no values for a
            (level-tuple)-keyed dictionary.

        Note:
            .flatten(levels=0) does nothing,
            .flatten(levels=1) compresses 1 level (i.e. keys will be 2-ples)

        Parameters
        ----------
        levels: int, default=1
            Number of levels to flatten by.
            Defaults to flattening one level
        named: bool
            Whether output key-tuples are namedtuples
        flattened_name: str
            Name of new flattened level. Defaults to original level
            names joined by "___"

        Returns
        -------
        StructuredNestedDict
        """
        levels = self._wrap_level(levels)
        if not self._level_names_is_set:
            new_level_names = None
        else:
            if flattened_name is None:
                flattened_name = FLATTENED_LEVEL_NAME_SEPARATOR.join(
                    self.level_names[:levels + 1]
                )
            new_level_names = (flattened_name,) + self.level_names[levels + 1:]

        return self.__class__(
            self.iterflatten(levels=levels, named=named),
            levels=self.levels - levels,
            level_names=new_level_names,
        )

    def flatten_keys(self, levels=1, named=True):
        """Returns an list with of keys of flattened dict

        WARNING:
            If there are empty dictionaries within the levels being flattened,
            their keys will be lost. This is consistent with the logic of
            flattening - those dictionaries contain no values for a
            (level-tuple)-keyed dictionary.

        Note:
            .flatten(levels=0) does nothing,
            .flatten(levels=1) compresses 1 level (i.e. keys will be 2-ples)

        Parameters
        ----------
        levels: int, default=1
            Number of levels to flatten by.
            Defaults to flattening one level
        named: bool
            Whether output key-tuples are namedtuples

        Returns
        -------
        list
        """
        levels = self._wrap_level(levels)
        return list(self.iterflatten_keys(levels=levels, named=named))

    def flatten_values(self, levels=-1):
        """Returns an list with of values of flattened dict

        WARNING:
            If there are empty dictionaries within the levels being flattened,
            their keys will be lost. This is consistent with the logic of
            flattening - those dictionaries contain no values for a
            (level-tuple)-keyed dictionary.

        Note:
            .flatten(levels=0) does nothing,
            .flatten(levels=1) compresses 1 level (i.e. keys will be 2-ples)

        Parameters
        ----------
        levels: int, default=-1
            Number of levels to flatten by.
            Defaults to flattening all levels.

        Returns
        -------
        list
        """
        levels = self._wrap_level(levels)
        return list(self.iterflatten_values(levels=levels))

    def unique_keys(self, named=False, sort_keys=True):
        """Returns the unique keys in each level of the dictionary

        Parameters
        ----------
        named: bool
            If True, return OrderedDict of list of keys of each level. If False,
            return a list of list of keys.
        sort_keys: bool
            Whether to sort each list of keys

        Returns
        -------
        list or dict
        """
        unique_keys = col.OrderedDict()

        this_level_dicts = [self]
        for level, level_name in enumerate(self.level_names):
            level_key_set = set()
            next_level_dicts = list()
            for level_dict in this_level_dicts:
                level_key_set.update(level_dict.keys())
                if level < self.levels - 1:
                    next_level_dicts += level_dict.values()
            this_level_dicts = next_level_dicts
            unique_keys[level_name] = list(level_key_set)
            if sort_keys:
                unique_keys[level_name].sort()

        if named:
            return unique_keys
        else:
            return unique_keys.values()

    # ==== Dict Transformation ==== #

    def stratify(self, levels=None, stratified_names=None):
        """Increases depth (nests) of StructuredNestedDict by splitting up
         keys in the top-most level

        Parameters
        ----------
        levels: int, default=None
            Number of levels to stratify by. Defaults to length of first key.
            Note: levels must be <= length of all top-level keys
        stratified_names: default=None
            Names of newly created stratified levels. Must be same length
            as levels.

        Returns
        -------
        StructuredNestedDict
        """
        try:
            levels = replace_none(levels, len(self.keys()[0]))
        except IndexError:
            raise LevelError("Cannot infer stratify-levels")

        # stratify 0 = nothing, stratify 1 = 1
        new_dict = col.OrderedDict()
        for key_tup, val in self.iteritems():
            stratified_keys = key_tup[:levels + 1]
            remaining_keys = key_tup[levels + 1:]

            dict_pointer = new_dict
            for key in stratified_keys[:-1]:
                if key not in dict_pointer:
                    dict_pointer[key] = col.OrderedDict()
                dict_pointer = dict_pointer[key]

            final_key = stratified_keys[-1]

            if len(remaining_keys):
                dict_pointer[final_key] = col.OrderedDict()
                dict_pointer[final_key][remaining_keys] = val
            else:
                dict_pointer[final_key] = val

        # TODO: Re-org into function
        remaining_names = self.level_names[1:]
        if stratified_names:
            # Need pre/post stratus name
            assert len(stratified_names) == levels + 1
            level_names = stratified_names + remaining_names
        else:
            candidate = tuple(self.level_names[0].split(
                FLATTENED_LEVEL_NAME_SEPARATOR
            ))
            if len(candidate) == levels + 1:
                level_names = candidate + remaining_names
            else:
                level_names = None

        return self.__class__(
            new_dict, levels=levels + self.levels,
            level_names=level_names,
        )

    def convert(self, dict_type=None):
        """Convert all nested dictionaries to desired type.

        Parameters
        ----------
        dict_type: ['sndict', 'ndict', 'dict', 'odict']
            Dict-type in string format

        Returns
        -------
        dict, OrderedDict or NestedDict
        """
        assert dict_type != "sndict", \
            "For converting underlying levels to sndict, consider using " \
            "sndict.new_with_metadata instead"

        return self._resolve_dict_type(dict_type)([
            (key, StructuredNestedDict(val).convert(dict_type)
                if isinstance(val, dict) else val)
            for key, val in self.iteritems()
        ])

    def rearrange(self, level_ls=None, level_name_ls=None):
        """Rearrange levels of StructuredNestedDict
        Only supply either level_ls or level_name_ls.

        Note: Whether supplying level_ls or level_name_ls, the supplied list
            must cover all levels contiguously from the start. I.e.

                level_ls=[2, 0, 1, 3]

            is valid but

                level_ls=[2, 0]

            is not.

        Parameters
        ----------
        level_ls: list
            List of level ints. If level_ls contains level_names instead, the
            arguments is passed on to level_name_ls
        level_name_ls: list
            List of level names

        Returns
        -------
        StructuredNestedDict
        """
        assert (level_ls is None) != (level_name_ls is None), \
            "Only either level_ls or level_name_ls can be supplied"

        if level_ls is not None:
            assert len(level_ls) > 0
            if not isinstance(level_ls[0], int):
                level_name_ls = level_ls
            else:
                assert set(level_ls) == set(range(len(level_ls)))

        if level_name_ls is not None:
            assert list_is_unique(level_name_ls)
            if not set(level_name_ls) == \
                    set(self.level_names[:len(level_name_ls)]):
                raise RuntimeError("Redimensioned level_name_ls must be "
                                   "contiguous from level 0")

            level_ls = [self.level_names.index(level_name)
                        for level_name in level_name_ls]

        return self._rearrange(level_ls)

    def _rearrange(self, level_ls):
        """Underlying method for rearranging levels"""
        num_levels = len(level_ls)

        new_dict = col.OrderedDict()
        for key_tup, val in self.iterflatten(num_levels - 1):
            new_dict[tuple(list_index(key_tup, level_ls))] = val

        if self._level_names_is_set:
            new_level_names = tuple(list_index(self.level_names, level_ls))\
                + self.level_names[num_levels:]
        else:
            new_level_names = None

        return self.__class__(new_dict, levels=self.levels - num_levels + 1)\
            .stratify((len(level_ls)) - 1)\
            .replace_metadata(level_names=new_level_names)

    def swap_levels(self, level_a, level_b):
        """Swap two levels in a StructuredNestedDict

        Unlike sndict.rearrange, there's no need to be contiguous

        Parameters
        ----------
        level_a: int or str
            level or level_name
        level_b: int or str
            level or level_name

        Returns
        -------
        StructuredNestedDict
        """
        if not isinstance(level_a, int):
            level_a = self.level_names.index(level_a)
        if not isinstance(level_b, int):
            level_b = self.level_names.index(level_b)

        assert level_a != level_b
        assert 0 <= level_a < self.levels
        assert 0 <= level_b < self.levels

        required_levels = max(level_a, level_b) + 1
        new_level_ls = range(required_levels)
        new_level_ls[level_b], new_level_ls[level_a] = \
            new_level_ls[level_a], new_level_ls[level_b]

        return self._rearrange(new_level_ls)

    def replace_metadata(self, **kwargs):
        """Return new StructuredNestedDict with different metadata but same data

        Parameters
        ----------
        levels: int
            Number of nested levels that StructuredNestedDict will work on
        level_names: list
            List of level names

        Returns
        -------
        StructuredNestedDict
        """
        assert set(kwargs.keys()) <= {"levels", "level_names"}
        return self.__class__(self, **kwargs)

    def replace_data(self, data):
        """Return new StructuredNestedDict with different data but same metadata

        Parameters
        ----------
        data: dict, or list
            Nested dictionary

        Returns
        -------
        StructuredNestedDict
        """
        return self.__class__(
            data, levels=self.levels,
            level_names=self._level_names if self._level_names_is_set else None,
        )

    def sort_keys(self, cmp=None, key=None, reverse=False):
        """Sort keys of StructuredNestedDict (top-level only)

        Parameters
        ----------
        cmp: function, optional
            Comparator function
        key: function, optional
            Key function
        reverse: bool, optional
            Whether to sort in reverse

        Returns
        -------
        StructuredNestedDict
        """
        return self.replace_data([
            (key, self[key])
            for key in sorted(self.keys(), cmp, key, reverse)
        ])

    def sort_values(self, cmp=None, key=None, reverse=False):
        """Sort values of StructuredNestedDict (top-level only)

        Parameters
        ----------
        cmp: function
            Comparator function
        key: function
            Key function
        reverse: bool
            Whether to sort in reverse

        Returns
        -------
        StructuredNestedDict
        """
        if cmp is not None:
            cmp = lambda a, b: cmp(a[1], b[1])

        if key is not None:
            key = lambda a: key(a[1])
        else:
            key = lambda a: a[1]

        return self.replace_data([
            (key, val)
            for key, val in sorted(self.items(), cmp, key, reverse)
        ])

    def map(self, key_func=None, val_func=None):
        """Apply transformations to keys and values

        Parameters
        ----------
        key_func: function, optional
            Function to transform keys. Defaults to identity.
        val_func: function, optional
            Function to transform values. Defaults to identity.

        Returns
        -------
        StructuredNestedDict
        """
        key_func = replace_none(key_func, identity)
        val_func = replace_none(val_func, identity)

        new_dict = self.replace_data([
            (key_func(key), val_func(val))
            for key, val in self.iteritems()
        ])

        # Confirm uniqueness of post key_func map
        assert len(new_dict) == len(self)

        return new_dict

    def map_keys(self, key_func):
        """Apply transformations to keys and values

        Parameters
        ----------
        key_func: function
            Function to transform keys

        Returns
        -------
        StructuredNestedDict
        """
        return self.map(key_func=key_func)

    def map_values(self, val_func):
        """Apply transformations to keys and values

        Parameters
        ----------
        val_func: function
            Function to transform values

        Returns
        -------
        StructuredNestedDict
        """
        return self.map(val_func=val_func)

    # ==== Setters, Getters and Selectors ==== #

    def filter_key(self, criteria_ls, filter_out=False, drop_empty=False):
        """Filter StructuredNestedDict by criteria.

        The criteria used in the following ways, based on type:
            1. slice(None): Keep all
            2. function: Keep if function(key) is True
            3. list, set: Keep if key in list/set
            4. other: Keep if key==other

        Parameters
        ----------
        criteria_ls: list or dict
            Filter based on criteria
        filter_out: bool
            Whether to filter in or out
        drop_empty:
            Whether to drop empty nested dictionaries (nested dictionaries
            with all elements filtered out)

        Returns
        -------
        StructuredNestedDict
        """
        if len(criteria_ls) == 0:
            raise KeyError("criteria_ls cannot be empty")

        if isinstance(criteria_ls, dict):
            new_criteria_dict = col.OrderedDict()
            for level_name in self.level_names:
                if level_name not in criteria_ls:
                    new_criteria_dict[level_name] = slice(None)
                else:
                    new_criteria_dict[level_name] = criteria_ls.pop(level_name)
            if criteria_ls:
                raise RuntimeError("Unused criteria for: {}".format(
                    criteria_ls.keys()
                ))
            criteria_ls = new_criteria_dict.values()

        filter_func_ls = [_get_filter_func(criteria, filter_out=filter_out)
                          for criteria in criteria_ls]
        return self._filter_key(self, filter_func_ls, drop_empty)

    @classmethod
    def _filter_key(cls, obj, filter_func_ls, drop_empty):
        """Underlying method for filter_key"""
        if not filter_func_ls or not isinstance(obj, StructuredNestedDict):
            return obj

        filter_func = filter_func_ls[0]

        new_dict = col.OrderedDict()
        for key, val in obj.iteritems():
            if not filter_func(key):
                continue
            new_val = cls._filter_key(val, filter_func_ls[1:], drop_empty)
            if drop_empty and isinstance(new_val, StructuredNestedDict) \
                    and len(new_val) == 0:
                continue
            new_dict[key] = new_val

        return obj.replace_data(new_dict)

    def filter_values(self, filter_func, filter_out=False,
                      level=None, drop_empty=False):
        if filter_out:
            filter_func = negate(filter_func)
        level = replace_none(level, self.levels - 1)

        return self._filter_values(self, filter_func, level, drop_empty)

    @classmethod
    def _filter_values(cls, obj, filter_func, levels_remaining, drop_empty):
        """Underlying method for filter_values"""

        if levels_remaining == 0:
            return obj.replace_data([
                (key, val)
                for (key, val) in obj.iteritems()
                if filter_func(val)
            ])
        else:
            new_dict = col.OrderedDict()
            for key, val in obj.iteritems():
                new_val = cls._filter_values(val, filter_func,
                                             levels_remaining - 1, drop_empty)
                if drop_empty and len(new_val) == 0:
                    continue
                new_dict[key] = new_val

            return obj.replace_data(new_dict)

    def nested_set(self, key_list, value):
        """Set a value within nested dicts, creating StructuredNestedDict at
        depth if they don't exist yet

        Note: Only allowed to set up to level of StructuredNestedDict

        Parameters
        ----------
        key_list: list
            List of keys, one for each dict depth
        value: object
            Value to set nested
        """
        self._check_key_list(key_list)
        dict_pointer = self
        for key in key_list[:-1]:
            if key not in dict_pointer:
                dict_pointer[key] = self.__class__()
            dict_pointer = dict_pointer[key]
        dict_pointer[key_list[-1]] = value

    def nested_setdefault(self, key_list, default=None):
        """Nested version of dict.setdefault. Set a value within nested dicts,
        creating StructuredNestedDict at depth if they don't exist yet

        Note: Only allowed to set up to level of StructuredNestedDict

        Parameters
        ----------
        key_list: list
            List of keys, one for each dict depth
        default: object, optional
            Value to set nested
        """
        self._check_key_list(key_list)
        if self.has_nested_key(key_list):
            return self.nested_get(key_list)
        else:
            self.nested_set(key_list, default)
            return default

    def nested_get(self, key_list):
        """Get value at depth

        Parameters
        ----------
        key_list: list
            List of keys, one for each dict depth

        Returns
        -------
        obj
        """
        self._check_key_list(key_list)
        pointer = self
        for key in key_list:
            pointer = pointer[key]
        return pointer

    def has_nested_key(self, key_list):
        """Check if nested keys are valid

        Parameters
        ----------
        key_list: list
            List of keys, one for each dict depth

        Returns
        -------
        bool
        """
        self._check_key_list(key_list)
        try:
            self.nested_get(key_list)
            return True
        except KeyError:
            return False

    def _get_multiple(self, key_or_criteria_ls):
        """Check whether list has keys or criteria (i.e. if any of the criteria
        lead to special filtering/getting functions"""
        if any(map(_is_criteria, key_or_criteria_ls)):
            return self.filter_key(criteria_ls=key_or_criteria_ls)\
                .flatten_values(len(key_or_criteria_ls) - 1)
        else:
            return self.nested_get(key_or_criteria_ls)

    def _set_multiple(self, key_or_criteria_ls, val):
        """Check whether list has keys or criteria (i.e. if any of the criteria
        lead to special setting functions"""
        # TODO: Currently implementation is lazy and suboptimal,
        #       repeatedly tests earlier keys
        if any(map(_is_criteria, key_or_criteria_ls)):
            selected_keys = self.filter_key(criteria_ls=key_or_criteria_ls)\
                .flatten_keys(len(key_or_criteria_ls) - 1)
            for key_ls in selected_keys:
                print key_ls
                self.nested_set(key_ls, val)
        else:
            self.nested_set(key_or_criteria_ls, val)

    @property
    def ixkeys(self):
        """Indexer that allows for indexing by nested key list e.g.

            my_ndict.ix["key1", "key2", "key3"]

        or with criteria such as

            my_sndict.ix["key1", :, lambda _: "3" in _]

        Note that for a single key, a tuple/list needs to be provided, e.g.

            my_sndict.ix["key1",]

        Returns
        -------
        Indexable
        """
        return GetSetFunctionClass(
            get_func=self._get_multiple,
            set_func=self._set_multiple,
        )

    @property
    def ix(self):
        """Indexer that allows for indexing by nested key/criteria list e.g.

            my_ndict.ix["key1", "key2", "key3"]

        or with criteria such as

            my_sndict.ix["key1", :, lambda _: "3" in _]

        Also supports:

            my_sndict.ix["key1"]

        If behavior is ambiguous, use sndict.ixkeys[key_list] and sndict[key]
        directly instead

        Returns
        -------
        Indexable
        """
        return GetSetAmbiguousTupleFunctionClass(
            get_func=self._get_multiple,
            set_func=self._set_multiple,
        )

    # ==== Other ==== #

    def __repr__(self):
        args_string_ls = [
            dict_to_string(self),
            "levels={levels}".format(levels=self._levels),
        ]

        if self._level_names_is_set:
            args_string_ls.append("level_names={level_names}".format(
                level_names=self.level_names
            ))

        return "{class_name}({args_string})".format(
            class_name=self.__class__.__name__,
            args_string=", ".join(args_string_ls),
        )

    def __setitem__(self, key, value):
        if self.levels > 1:
            if isinstance(value, StructuredNestedDict) \
                    and value.levels == self.levels - 1 \
                    and value.level_names[1:] == self.level_names[1:]:
                # If dictionary is already StructuredNestedDict, and it looks
                # like we expect it to, skip overhead of initializing anew
                pass
            elif isinstance(value, dict):
                value = StructuredNestedDict(
                    value, levels=self.levels - 1,
                    level_names=self.level_names[1:]
                    if self._level_names_is_set else None,
                )

            if not isinstance(value, StructuredNestedDict) or \
                    value.levels != self.levels - 1:
                raise TypeError(
                    "Inserted item needs to be a StructuredNestedDict "
                    "with level={}".format(self.levels - 1))

        super(self.__class__, self).__setitem__(key, value)

    def to_tree_string(self, indent=" - ",
                       key_mode="str",
                       val_mode="type"):
        """Returns structure of NestedDict in tree format string

        Parameters
        ----------
        indent: str
            Indentation string for levels
        key_mode: "type", "str" or "repr"
            How to serialize key
        val_mode: "type", "str" or "repr"
            How to serialize terminal value

        Returns
        -------
        str
        """
        key_str = get_str_func(key_mode)
        val_str = get_str_func(val_mode)

        def _dfs_print(dictionary, level, indent_):
            string_ = ""
            if level > 0:
                indent_str = "  " * (level - 1) + "'-"
            else:
                indent_str = ""
            for key, val in dictionary.iteritems():
                if level < self.levels - 1:
                    string_ += "{}{}:\n".format(
                        indent_str, key_str(key))
                    string_ += _dfs_print(val, level + 1, indent_)
                else:
                    string_ += "{}{}: {}\n".format(
                        indent_str, key_str(key), val_str(val))
            return string_
        return _dfs_print(self, 0, indent)

    def get_named_tuple(self, levels):
        """Get namedtuple class for named keys

        Parameters
        ----------
        levels: Number of levels to construct named keys for

        Returns
        -------
        class
        """
        return col.namedtuple("KeyTuple", self.level_names[:levels])

    @staticmethod
    def _resolve_dict_type(dict_type):
        """Resolve dict type based on string

        Parameters
        ----------
        dict_type: ['sndict', 'ndict', 'dict', 'odict']
            Dict-type in string format

        Returns
        -------
        class
        """
        if dict_type in [dict, col.OrderedDict, StructuredNestedDict]:
            dict_class = dict_type
        elif dict_type is None or dict_type == "sndict":
            dict_class = StructuredNestedDict
        elif dict_type == "ndict":
            dict_class = NestedDict
        elif dict_type == "dict":
            dict_class = dict
        elif dict_type == "odict":
            dict_class = col.OrderedDict
        else:
            raise KeyError(dict_type)
        return dict_class

    @staticmethod
    def _check_key_list(key_list):
        """Check if key_list is valid"""
        if len(key_list) == 0:
            raise KeyError("key_list cannot be empty")

    def _wrap_level(self, level):
        """Wrap a level argument"""
        return _wrap_level(level, allowed_level=self.levels)


def _wrap_level(level, allowed_level):
    """Wrap levels given a maximum allowed level"""
    if level < 0:
        wrapped_level = allowed_level + level
    else:
        wrapped_level = level

    if wrapped_level < 0 or wrapped_level >= allowed_level:
        raise LevelError(
            "Level {level} not valid for allowed_levels {allowed_level}".format(
                level=level, allowed_level=allowed_level
            ))
    return wrapped_level


def _get_filter_func(criteria, filter_out=False):
    """Create filter function from criteria, based on type"""
    if criteria == slice(None):
        filter_func = lambda x: True
    elif isinstance(criteria, types.FunctionType):
        filter_func = criteria
    elif isinstance(criteria, (list, set)):
        filter_func = lambda x: x in criteria
    else:
        filter_func = lambda x: x == criteria

    if filter_out:
        filter_func = negate(filter_func)

    return filter_func


def _is_criteria(key_or_criteria):
    """Check if argument is a key or filter-criteria"""
    if key_or_criteria == slice(None):
        return True
    elif isinstance(key_or_criteria, (list, set, types.FunctionType)):
        return True
    else:
        return False

sndict = StructuredNestedDict
