import collections as col

from utils import (
    GetSetFunctionClass, GetSetAmbiguousTupleFunctionClass,
    dict_to_string, get_str_func
)


class NestedDict(col.OrderedDict):

    def __init__(self, *args, **kwargs):
        """Extension of OrderedDict that exposes operations on nested dicts

        Parameters
        ----------
        args
        kwargs
        """
        super(self.__class__, self).__init__(*args, **kwargs)

    @classmethod
    def from_flat(cls, data, dict_type="ndict"):
        """Initialize from a dict keyed by tuples
        Each tuple-element is taken as a key for each level in the NestedDict

        Parameters
        ----------
        data: dict
            Dictionary keyed by tuples
        dict_type: ['ndict', 'dict', 'odict']
            Dict-type in string format, for initializing dicts at depth if they
            don't exist yet

        Returns
        -------
        NestedDict
        """
        new_dict = cls()
        for key_list, val in data.iteritems():
            new_dict.nested_set(key_list, val, dict_type=dict_type)
        return new_dict

    # ==== Iterators ==== #

    def iterflatten(self, max_depth=None):
        """Iterate over a flattened NestedDict. For each value, keys along the
          DFS are accumulated as a tuple

        Parameters
        ----------
        max_depth: int, optional
            Maximum depth to flatten by, i.e. the maximum key-tuple length

        Returns
        -------
        iterator
            Iterator of (key-tuple, value) pairs
        """
        return self._iterflatten(self, max_depth=max_depth)

    @classmethod
    def _iterflatten(cls, dictionary, max_depth=None, depth=1):
        """DFS method for flattening a NestedDict"""
        assert depth > 0
        for key, val in dictionary.iteritems():
            if isinstance(val, dict) \
                    and (max_depth is None or depth < max_depth):
                for partial_key_tup, sub_val in NestedDict._iterflatten(
                        val, max_depth=max_depth, depth=depth+1):
                    yield (key,) + partial_key_tup, sub_val
            else:
                yield (key, ), val

    def iterflatten_keys(self, max_depth=None):
        """Iterate over a flattened NestedDict, and expose only keys.
        Keys along the DFS are accumulated as a tuple

        Parameters
        ----------
        max_depth: int, optional
            Maximum depth to flatten by, i.e. the maximum key-tuple length

        Returns
        -------
        iterator
            Iterator of key-tuples
        """
        for key, _ in self.iterflatten(max_depth=max_depth):
            yield key

    def iterflatten_values(self, max_depth=None):
        """Iterate over a flattened NestedDict, and expose only values.

        Parameters
        ----------
        max_depth: int, optional
            Maximum depth to flatten by

        Returns
        -------
        iterator
            Iterator of values
        """
        for _, val in self.iterflatten(max_depth=max_depth):
            yield val

    def flatten(self, max_depth=None):
        """Iterate over a flattened NestedDict. For each value, keys along the
          DFS are accumulated as a tuple

        Parameters
        ----------
        max_depth: int, optional
            Maximum depth to flatten by, i.e. the maximum key-tuple length

        Returns
        -------
        list
            List of (key-tuple, value) pairs
        """
        return list(self.iterflatten(max_depth=max_depth))

    def flatten_keys(self, max_depth=None):
        """Iterate over a flattened NestedDict, and expose only keys.
        Keys along the DFS are accumulated as a tuple

        Parameters
        ----------
        max_depth: int, optional
            Maximum depth to flatten by, i.e. the maximum key-tuple length

        Returns
        -------
        list
            List of key-tuples
        """
        return list(self.iterflatten_keys(max_depth=max_depth))

    def flatten_values(self, max_depth=None):
        """Iterate over a flattened NestedDict, and expose only values.

        Parameters
        ----------
        max_depth: int, optional
            Maximum depth to flatten by

        Returns
        -------
        list
            List of values
        """
        return list(self.iterflatten_values(max_depth=max_depth))

    # ==== Dict Transformation ==== #

    def map_values(self, val_func):
        """Apply transformations to keys and values

        Parameters
        ----------
        val_func: function
            Function to transform values

        Returns
        -------
        NestedDict
        """
        new_dict = self.__class__()
        for key, val in self.iteritems():
            new_dict.nested_set(key, val_func(val), dict_type="ndict")

        return new_dict

    # ==== Setters and Getters ==== #

    def nested_set(self, key_list, value, dict_type="ndict"):
        """Set a value within nested dicts, creating dicts at depth if they
        don't exist yet

        Parameters
        ----------
        key_list: list
            List of keys, one for each dict depth
        value: object
            Value to set nested
        dict_type: ['ndict', 'dict', 'odict']
            Dict-type in string format, for initializing dicts at depth if they
            don't exist yet
        """
        self._check_key_list(key_list)
        dict_class = self._resolve_dict_type(dict_type)
        dict_pointer = self
        for key in key_list[:-1]:
            if key not in dict_pointer:
                dict_pointer[key] = dict_class()
            dict_pointer = dict_pointer[key]
        dict_pointer[key_list[-1]] = value

    def nested_setdefault(self, key_list, default=None, dict_type="ndict"):
        """Nested version of dict.setdefault, where a value is set only if
        it doesn't already exist, creating dicts at depth if they don't exist
        yet

        Parameters
        ----------
        key_list: list
            List of keys, one for each dict depth
        default: object
            Value to set nested
        dict_type: ['ndict', 'dict', 'odict']
            Dict-type in string format, for initializing dicts at depth if they
            don't exist yet
        """
        self._check_key_list(key_list)
        if self.has_nested_key(key_list):
            return self.nested_get(key_list)
        else:
            self.nested_set(key_list, default, dict_type=dict_type)
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

    def nested_update(self, other_dict):
        """Nested version of dict.update. Changes NestedDict in-place

        Parameters
        ----------
        other_dict: dict
            dict to update by.
        """
        other_dict = NestedDict(other_dict)
        for key_tup, val in other_dict.flatten():
            self.nested_set(key_tup, val)

    @staticmethod
    def _check_key_list(key_list):
        """Check if key_list is valid"""
        if len(key_list) == 0:
            raise KeyError("key_list cannot be empty")

    @property
    def ixkeys(self):
        """Indexer that allows for indexing by nested key list e.g.

            my_ndict.ix["key1", "key2", "key3"]

        Note that for a single key, a tuple/list needs to be provided, e.g.

            my_ndict.ix["key1",]

        Returns
        -------
        Indexable
        """
        return GetSetFunctionClass(
            get_func=self.nested_get,
            set_func=self.nested_set,
        )

    @property
    def ix(self):
        """Indexer that allows for indexing by nested key list e.g.

            my_ndict.ix["key1", "key2", "key3"]

        Also supports:

            my_ndict.ix["key1"]

        If behavior is ambiguous, use ndict.ixkeys[key_list] and ndict[key]
        directly instead

        Returns
        -------
        Indexable
        """
        return GetSetAmbiguousTupleFunctionClass(
            get_func=self.nested_get,
            set_func=self.nested_set,
        )

    # ==== Conversion ==== #

    def convert(self, dict_type=None):
        """Convert all nested dictionaries to desired type.

        Parameters
        ----------
        dict_type: ['ndict', 'dict', 'odict']
            Dict-type in string format

        Returns
        -------
        dict, OrderedDict or NestedDict
        """

        return self._resolve_dict_type(dict_type)([
            (key, NestedDict(val).convert(dict_type)
                if isinstance(val, dict) else val)
            for key, val in self.iteritems()
        ])

    # ==== Other ==== #

    def __repr__(self):
        return "{class_name}({data})".format(
            class_name=self.__class__.__name__,
            data=dict_to_string(self),
        )

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
                if isinstance(val, dict):
                    string_ += "{}{}:\n".format(
                        indent_str, key_str(key))
                    string_ += _dfs_print(val, level + 1, indent_)
                else:
                    string_ += "{}{}: {}\n".format(
                        indent_str, key_str(key), val_str(val))
            return string_
        return _dfs_print(self, 0, indent)

    @staticmethod
    def _resolve_dict_type(dict_type):
        """Resolve dict type based on string

        Parameters
        ----------
        dict_type: ['ndict', 'dict', 'odict']
            Dict-type in string format

        Returns
        -------
        class
        """
        if dict_type in [dict, col.OrderedDict, NestedDict]:
            dict_class = dict_type
        elif dict_type is None or dict_type == "ndict":
            dict_class = NestedDict
        elif dict_type == "dict":
            dict_class = dict
        elif dict_type == "odict":
            dict_class = col.OrderedDict
        else:
            raise KeyError(dict_type)
        return dict_class


ndict = NestedDict
