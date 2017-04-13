Examples
========

Navigating Directory Structures with NestedDict
-----------------------------------------------

We can obtain the directory tree of the ``sndict`` repo like so:

```python
import os
import sndict

directory_tree = sndict.app.directory_tree(os.path.join(os.path.dirname(sndict.__file__), ".."))
```

Unfortunately, this includes various files/folders that we don't want, for example the .git folder docs/build folders. We can just delete those:

```python
del directory_tree[".git"]
del directory_tree["docs"]["build"]
```

This still leaves us with ".pyc" files. We can remove them using ``filter_values``. We can then calculate the file-size of every file in the repo, and print it as a readable tree-string.


```python
print directory_tree\
    .filter_values(lambda _: ".pyc" in _, filter_out=True)\
    .map_values(lambda _: os.stat(_).st_size)\
    .to_tree_string()

#  Output:
#
#  .gitignore: 49
#  .travis.yml: 1057
#  AUTHORS.rst: 97
#  CONTRIBUTING.rst: 3216
#  HISTORY.rst: 275
#  LICENSE: 1071
#  MANIFEST.in: 264
#  Makefile: 2291
#  README.rst: 1920
#  docs:
#  '-Makefile: 6762
#  '-app.rst: 67
#  '-authors.rst: 28
#  '-conf.py: 8491
#  '-contributing.rst: 33
#  '-examples.rst: 895
#  '-history.rst: 28
#  '-index.rst: 235
#  '-installation.rst: 1099
#  '-make.bat: 6459
#  '-ndict.rst: 253
#  '-readme.rst: 27
#  '-sndict.rst: 508
#  '-usage.rst: 131
#  requirements_dev.txt: 145
#  setup.cfg: 339
#  setup.py: 1529
#  sndict:
#  '-__init__.py: 207
#  '-app.py: 754
#  '-exceptions.py: 41
#  '-nesteddict.py: 13783
#  '-shared.py: 535
#  '-structurednesteddict.py: 35819
#  '-utils.py: 6472
#  tests:
#  '-__init__.py: 0
#  '-test_nesteddict.py: 4111
#  '-test_shared.py: 456
#  '-test_structurednesteddict.py: 10624
#  tox.ini: 395
#  travis_pypi_setup.py: 3751

```