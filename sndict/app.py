import os

from .utils import split_path
from .nesteddict import NestedDict
from .structurednesteddict import StructuredNestedDict


def directory_tree(base_path):
    """Compute directory tree as NestedDict

    Parameters
    ----------
    base_path: Starting path directory Tree

    Returns
    -------
    NestedDict
    """
    path_ndict_data = []

    path_stub_len = len(split_path(base_path))
    for dirpath, dirnames, filenames in list(os.walk(base_path)):
        dir_stub_tup = tuple(split_path(dirpath)[path_stub_len:])
        for filename in filenames:
            path_ndict_data.append(
                (dir_stub_tup + (filename,), os.path.join(dirpath, filename))
            )

    return NestedDict.from_flat(sorted(path_ndict_data))
