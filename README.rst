====
Home
====


.. image:: https://img.shields.io/pypi/v/sndict.svg
        :target: https://pypi.python.org/pypi/sndict

.. image:: https://img.shields.io/travis/zphang/sndict.svg
        :target: https://travis-ci.org/zphang/sndict

.. image:: https://readthedocs.org/projects/sndict/badge/?version=latest
        :target: https://sndict.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/zphang/sndict/shield.svg
     :target: https://pyup.io/repos/github/zphang/sndict/
     :alt: Updates


Nested Extensions to Python dictionaries

* Free software: MIT license
* Documentation: https://sndict.readthedocs.io
* Code: https://github.com/zphang/sndict


Introduction
------------
This module provides extensions to ``dicts`` in the python standard library, providing fast and clean manipulation of nested dictionary structures. This module exposes two new ``dict``-types:

* ``NestedDict``/``ndict``: A light-weight wrapper for ``dict`` s that provides additional functionality for operations on nested dictionary structures.
* ``StructuredNestedDict``/``sndict``: A heavy-weight data ``dict`` -based structure for operating on hierarchical data with rich functionality for filtering and transformation across nested levels.

Both implementations are use ``OrderedDict`` s under the hood.

No additional dependencies are required.

Features
--------

* ``NestedDict``/``ndict``:
    - Iterating over flattened keys and values
    - Nested getting/setting operations
    - Applicable to dictionaries of arbitrary and unbalanced depth

* ``StructuredNestedDict``/``sndict``:
    - ``flatten``/``stratify``/``rearrange`` methods allow for powerful and rich operations across different levels of hierarchy
    - Nested getting/setting operations, including intelligent filtering via ``ix``
    - Convenient data inspection via ``dim``, ``unique_keys``, etc
