## Introduction

This module provides extensions to `dicts` in the python standard library, providing fast and clean manipulation of nested dictionary structures. This module exposes two new `dict`-types: `NestedDict`/`ndict` and `StructuredNestedDict`/`sndict`/

## NestedDict / ndict



## Features

* Convenience methods for transforming keys (`XDict.key_map`), values, (`XDict.val_map`), and getting/setting elements at depth (`XDict.get_chain`, (`XDict.set_chain`)
* Collapsing and expanding nested levels (`XDict.flatten`, `XDict.stratify`)
* Reordering nested layers (`XDict.reorder_levels`, `XDict.swap_levels`)
* Variants of operations that operate at specific depth (e.g. `XDict.flatten_at`)

Used in conjunction, these allow for short but powerful transformations and operations on nested data structures.

## Examples


## Caveats and Warnings
* **This module is new, untested, and very much subject to change.**
* Sort at multiple levels