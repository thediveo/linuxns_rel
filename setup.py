#!/usr/bin/env python3

from distutils.core import setup
from linuxns_rel import __version__

setup(
    name='linuxns-rel',
    version=__version__,
    description='Linux namespace relationships library',
    classifiers=[
        'Development Status :: 4 - Beta',
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
    entry_points= {
        'console_scripts': [
            'lsuserns=linuxns_rel.tools.lshierns:lsuserns',
            'lspidns=linuxns_rel.tools.lshierns:lspidns'
        ]
    }
)
