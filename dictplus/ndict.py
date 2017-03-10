import collections as col

from utils import list_add


class NDict(col.OrderedDict):
    def __init__(self, *args, **kwargs):
        self._levels = kwargs.pop("levels", 1)
        super(self.__class__, self).__init__(*args, **kwargs)
        self._dim = self._convert(self, levels=self._levels - 1)

    @property
    def dim(self):
        return self._dim

    @classmethod
    def _convert(cls, obj, levels):
        if levels == 0:
            return len(obj),

        dim_list = [[0] * (levels + 1)]
        for key, val in obj.iteritems():
            if isinstance(val, NDict):
                new_nested_dict = val
            else:
                new_nested_dict = NDict(val, levels=levels)
            obj[key] = new_nested_dict
            dim_list.append([1] + list(new_nested_dict.dim))
        return tuple(list_add(dim_list))

    def flatten(self, levels=1):
        return self.__class__(self.iterflatten(levels=levels))

    def iterflatten(self, levels=1):
        for key_ls, val in self._iterflatten(levels=levels):
            yield tuple(key_ls), val

    def _iterflatten(self, levels):
        # flatten 0 = nothing, flatten 1 = 1
        for key, val in self.iteritems():
            # TODO: stop levels from being too deep
            if levels > 0:
                if not isinstance(val, NDict):
                    raise RuntimeError()
                for sub_key_ls, sub_val in val._iterflatten(levels - 1):
                    yield [key] + sub_key_ls, sub_val
            else:
                yield [key], val

    def stratify(self):
        pass
