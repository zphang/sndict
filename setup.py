#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    # TODO: put package requirements here
    six,
]

test_requirements = [
    # TODO: put package tests requirements here
]

setup(
    name='sndict',
    version='0.1.2',
    description="Nested Extensions to Python dictionaries",
    long_description=readme + '\n\n' + history,
    author="Jason Phang",
    author_email='email@jasonphang.com',
    url='https://github.com/zphang/sndict',
    packages=[
        'sndict',
    ],
    entry_points={
        'console_scripts': [
            'sndict=sndict.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='sndict',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
