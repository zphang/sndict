import collections as col

from utils import GetSetFunctionClass, dict_to_string


class NestedDict(col.OrderedDict):

    def iterflatten(self, max_depth=None):
        return self._iterflatten(self, max_depth=max_depth)

    @classmethod
    def _iterflatten(cls, dictionary, max_depth=None, depth=1):
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
        for key, _ in self.iterflatten(max_depth=max_depth):
            yield key

    def iterflatten_values(self, max_depth=None):
        for _, val in self.iterflatten(max_depth=max_depth):
            yield val

    def flatten(self, max_depth=None):
        return list(self.iterflatten(max_depth=max_depth))

    def flatten_keys(self, max_depth=None):
        return list(self.iterflatten_keys(max_depth=max_depth))

    def flatten_values(self, max_depth=None):
        return list(self.iterflatten_values(max_depth=max_depth))

    def convert(self, dict_type=None):
        """Convert all nested dictionaries to desired type.

        Parameters
        ----------
        dict_type: str (dict, odict, NestedDict)
            dict type to convert to

        Returns
        -------
        dict, OrderedDict or XDict
        """

        return self._resolve_dict_type(dict_type)([
            (key, NestedDict(val).convert(dict_type)
                if isinstance(val, dict) else val)
            for key, val in self.iteritems()
        ])

    @staticmethod
    def _resolve_dict_type(dict_type):
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

    def nested_set(self, key_list, value, dict_type="ndict"):
        self._check_key_list(key_list)
        dict_class = self._resolve_dict_type(dict_type)
        dict_pointer = self
        for key in key_list[:-1]:
            if key not in dict_pointer:
                dict_pointer[key] = dict_class()
            dict_pointer = dict_pointer[key]
        dict_pointer[key_list[-1]] = value

    def nested_setdefault(self, key_list, default=None, dict_type="ndict"):
        self._check_key_list(key_list)
        if self.has_nested_key(key_list):
            return self.nested_get(key_list)
        else:
            self.nested_set(key_list, default, dict_type=dict_type)
            return default

    def nested_get(self, key_list):
        self._check_key_list(key_list)
        pointer = self
        for key in key_list:
            pointer = pointer[key]
        return pointer

    def has_nested_key(self, key_list):
        self._check_key_list(key_list)
        try:
            self.nested_get(key_list)
            return True
        except KeyError:
            return False

    def nested_update(self, other_dict):
        other_dict = NestedDict(other_dict)
        for key_tup, val in other_dict.flatten():
            self.nested_set(key_tup, val)

    @staticmethod
    def _check_key_list(key_list):
        if len(key_list) == 0:
            raise KeyError("key_list cannot be empty")

    def __str__(self):
        return "{class_name}({data})".format(
            class_name=self.__class__.__name__,
            data=dict_to_string(self),
        )

    @property
    def ix(self):
        return GetSetFunctionClass(
            get_func=self.nested_get,
            set_func=self.nested_set,
        )


ndict = NestedDict
