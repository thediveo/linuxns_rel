# Copyright 2018 Harald Albrecht
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.


import linuxns_rel as nsr
import os
import unittest
from typing import Tuple, TextIO


class LxNsRelationsTests(unittest.TestCase):
    """Abstract base class bringing in some useful helpers for
    namespace unit tests."""

    NAMESPACES = (
        ('cgroup', nsr.CLONE_NEWCGROUP),
        ('ipc', nsr.CLONE_NEWIPC),
        ('mnt', nsr.CLONE_NEWNS),
        ('net', nsr.CLONE_NEWNET),
        ('pid', nsr.CLONE_NEWPID),
        ('user', nsr.CLONE_NEWUSER),
        ('uts', nsr.CLONE_NEWUTS)
    )  # type: Tuple[Tuple[str, int]]

    @staticmethod
    def nspath(type_name: str, pid: int=0) -> str:
        """Returns filesystem path to the namespace of the specified
        type for the current process (such as 'net', 'user', et
        cetera)."""
        return '/proc/%s/ns/%s' % (
                str(pid) if pid else 'self',
                type_name)

    @staticmethod
    def nsid(type_name_or_path: str) -> int:
        """Returns the namespace identifier (inode number) of the
        namespace specified either by type ('net', 'user') or by
        filesystem path ('/proc/self/ns/pid')."""
        if '/' not in type_name_or_path:
            type_name_or_path = LxNsRelationsTests.nspath(
                type_name_or_path)
        return os.stat(type_name_or_path).st_ino

    @staticmethod
    def file_nsid(file: TextIO) -> int:
        """Return the namespace identifier (inode number) of the
        namespace specified by a file."""
        return os.stat(file.fileno()).st_ino
