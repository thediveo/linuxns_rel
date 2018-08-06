#!/usr/bin/env python3

from setuptools import setup
from linuxns_rel import __version__
import os

with open(os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'README.md'
          )) as f:
    ldesc = f.read()

setup(
    name='linuxns-rel',
    version=__version__,
    description='Linux namespace relationships library',
    long_description=ldesc,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Operating System Kernels :: Linux'
    ],
    license='Apache License 2.0',
    author='TheDiveO',
    author_email='thediveo@gmx.eu',
    url='https://github.com/TheDiveO/linuxns_rel',
    packages=['linuxns_rel', 'linuxns_rel.tools'],
    entry_points={
        'console_scripts': [
            'lsuserns=linuxns_rel.tools.lshierns:lsuserns',
            'lspidns=linuxns_rel.tools.lshierns:lspidns',
            'graphns=linuxns_rel.tools.lshierns:graphns'
        ]
    },
    install_requires=[
        'psutil',
        'asciitree',
        'graphviz',
        'PyQt5'
    ],
    extras_require={
        'dev': [
            'coverage',
            'sphinx',
            'sphinx_rtd_theme'
        ]
    }
)
