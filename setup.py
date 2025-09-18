#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
$ python setup.py register sdist upload

First Time register project on pypi
https://pypi.org/manage/projects/


Pypi Release
$ pip3 install twine

$ python3 setup.py sdist
$ twine upload dist/signifypy-0.0.1.tar.gz

Create release git:
$ git tag -a v0.4.2 -m "bump version"
$ git push --tags
$ git checkout -b release_0.4.2
$ git push --set-upstream origin release_0.4.2
$ git checkout main

Best practices for setup.py and requirements.txt
https://caremad.io/posts/2013/07/setup-vs-requirement/
"""

from glob import glob
from os.path import basename
from os.path import splitext
from pathlib import Path

from setuptools import find_packages, setup

# Prepares a nice long description for PyPi based on the README.md file
this_directory = Path(__file__).parent
if (this_directory / "README.md").exists():  # If building inside a container this file won't exist and fails the build
    long_description = (this_directory / "README.md").read_text()
else:
    long_description = "KERI Signing at the Edge Infrastructure"

setup(
    name='signifypy',
    version='0.2.0',  # also change in src/signify/__init__.py
    license='Apache Software License 2.0',
    description='SignifyPy: KERI Signing at the Edge',
    long_description=long_description,
    author='Philip S. Feairheller',
    author_email='pfeairheller@gmail.com',
    url='https://github.com/WebOfTrust/signifypy',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Utilities',
    ],
    project_urls={
        'Documentation': 'https://signifypy.readthedocs.io/',
        'Changelog': 'https://signifypy.readthedocs.io/en/latest/changelog.html',
        'Issue Tracker': 'https://github.com/WebOfTrust/signifypy/issues',
        'Source': 'https://github.com/WebOfTrust/signifypy',
    },
    keywords=[
        "signing at the eddge",
        "signify",
        "secure attribution",
        "authentic data",
        "discovery",
        "resolver"
    ],
    python_requires='>=3.12.6',
    install_requires=[
        'keri==1.2.7',
        'multicommand==1.0.0',
        'requests==2.32.3',
        'http_sfv==0.9.9',
        'msgpack==1.1.0',
        'cbor2>=5.6.5',
        'sseclient>=0.0.27'
    ],
    extras_require={
        'test': [
            'responses>=0.25.6',
            'coverage>=7.6.10',
            'pytest>=8.3.4',
            'mockito==1.5.3'
        ],
    },
    tests_require=[
        'responses>=0.25.6',
        'coverage>=7.6.10',
        'pytest>=8.3.4',
        'mockito==1.5.3'
    ],
    setup_requires=[],
    entry_points={
        'console_scripts': [
            'sigpy = signify.app.cli.sigpy:main',
        ]
    },
)

