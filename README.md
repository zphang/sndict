## Introduction

XDict is a module that enables fast and clean manipulation of nested dictionary structures.

## Features

* Convenience methods for transforming keys (`XDict.key_map`), values, (`XDict.val_map`), and getting/setting elements at depth (`XDict.get_chain`, (`XDict.set_chain`)
* Collapsing and expanding nested levels (`XDict.flatten`, `XDict.stratify`)
* Reordering nested layers (`XDict.reorder_levels`, `XDict.swap_levels`)
* Variants of operations that operate at specific depth (e.g. `XDict.flatten_at`)

Used in conjunction, these allow for short but powerful transformations and operations on nested data structures.

## Examples


## Caveats and Warnings
* **This module is new, untested, and very much subject to change.**
* XDict primarily works with nested dictionary of *constant depth*. While many of XDict's method may work at shallow levels, no guarantees can be made if XDict is called on a unbalanced dictionary. This is an example of a dictionary for which no guarantees can be made past the first level:

    ```python
    XDict({
        "key1": {
            "key1_1": "val1_1",
            "key1_2": "val1_2",
        },
        "key2": "val2",
    })
    ```
    * Additionally, nested empty dictionaries are likely to confuse XDict, either by losing corresponding information or miscalculating dimensions. `XDict.flatten` is the primary operation that causes information on nested empty dictionaries to be lost. Because `XDict.flatten` is frequently used internally, few guarantees can be made about empty dictionaries. Here is an example where empty dictionary information is lost.
    ```python
    >>> XDict({
        "key1": {
            "key1_1": "val1_1",
            "key1_2": "val1_2",
        },
        "key2": dict()
    }).flatten().stratify()

    {'key1': {'key1_1': 'val1_1', 'key1_2': 'val1_2'}}
    ```

    * **In other words, XDict should only be used for nested dictionaries of consistent depth.**
* XDicts are internally `OrderedDicts`. As far as I can tell, there isn't too great a performance hit from using `OrderedDicts` rather than `dicts`. If this changes I may supply two different XDict classes.
* On calling the XDict constructor, the conversion of nested dictionaries to XDicts is done lazily. This is for performance reasons - repeatedly converting nested dictionaries can be costly, especially the dictionary is large and many operations are called that involve recreating dictionaries.

## Possible Road-map

* Naming levels
* Think about better handling unbalanced-depth dictionaries