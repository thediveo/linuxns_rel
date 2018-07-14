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
import unittest
from typing import Tuple


class LxNsRelationsBaseTests(unittest.TestCase):

    NAMESPACES = (
        ('cgroup', nsr.CLONE_NEWCGROUP),
        ('ipc', nsr.CLONE_NEWIPC),
        ('mnt', nsr.CLONE_NEWNS),
        ('net', nsr.CLONE_NEWNET),
        ('pid', nsr.CLONE_NEWPID),
        ('user', nsr.CLONE_NEWUSER),
        ('uts', nsr.CLONE_NEWUTS)
    )  # type: Tuple[Tuple[str, int]]

    def nspath(self, ns_type: str) -> str:
        """Returns filesystem path to the namespace of the specified
        type for the current process."""
        return '/proc/self/ns/%s' % ns_type

    def test_nstype_str(self):
        for ns_name, ns_type in self.NAMESPACES:
            self.assertEqual(
                nsr.nstype_str(ns_type),
                ns_name,
                'invalid name "%s" returned for '
                'namespace type value %d/%s' % (
                    nsr.nstype_str(ns_type),
                    ns_type,
                    hex(ns_type)
                )
            )

    def test_nstype_str_illegal_arg(self):
        with self.assertRaises(
                ValueError,
                msg='accepts invalid namespace type value'):
            nsr.nstype_str(42)

    def test_get_nstype(self):
        for ns_name, ns_type in self.NAMESPACES:
            # by path...
            self.assertEqual(
                nsr.get_nstype(self.nspath(ns_name)),
                ns_type,
                'invalid namespace type returned '
                'for "%s" namespace path' % ns_name
            )
            with open(self.nspath(ns_name)) as f:
                # by file...
                self.assertEqual(
                    nsr.get_nstype(f),
                    ns_type,
                    'invalid namespace type returned '
                    'for "%s" file' % ns_name
                )
                # by fd...
                self.assertEqual(
                    nsr.get_nstype(f.fileno()),
                    ns_type,
                    'invalid namespace type returned '
                    'for "%s" fd' % ns_name
                )

    def test_get_nstype_illegal_arg(self):
        with self.assertRaises(
                TypeError,
                msg='accepting float namespace reference parameter'):
            nsr.get_nstype(42.0)
        with self.assertRaises(
                TypeError,
                msg='accepting None namespace reference parameter'):
            nsr.get_nstype(None)