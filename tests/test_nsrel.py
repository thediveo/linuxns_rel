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

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring,missing-function-docstring

import errno

import linuxns_rel as nsr
import tests.linuxnsrel


class LxNsRelationsBaseTests(tests.linuxnsrel.LxNsRelationsTests):

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

    def test_get_userns(self):
        user_nsid = self.nsid('user')
        # by path...
        with nsr.get_userns(self.nspath('net')) as owner_ns:
            self.assertEqual(
                self.file_nsid(owner_ns),
                user_nsid,
                'invalid owning user namespace returned'
            )
        with open(self.nspath('net')) as nsref:
            # by file...
            with nsr.get_userns(nsref) as owner_ns:
                self.assertEqual(
                    self.file_nsid(owner_ns),
                    user_nsid,
                    'invalid owning user namespace returned'
                )
            # by fd...
            with nsr.get_userns(nsref.fileno()) as owner_ns:
                self.assertEqual(
                    self.file_nsid(owner_ns),
                    user_nsid,
                    'invalid owning user namespace returned'
                )

    def test_get_userns_illegal_arg(self):
        with self.assertRaises(
                TypeError, msg='accepts invalid namespace value'):
            nsr.get_userns(42.0)

    def test_getparentns_in_root(self):
        with self.assertRaises(
                PermissionError, msg='parent of root user'):
            nsr.get_parentns(self.nspath('user'))

    def test_getparentns_nonhierarchical_namespace(self):
        with self.assertRaises(
                OSError, msg='net namespace has a parent, seriously?')\
                as oserr:
            nsr.get_parentns(self.nspath('net'))
        self.assertEqual(
            oserr.exception.errno, errno.EINVAL,
            'no parent for non-hierarchical namespace'
        )

    def test_getparentns_illegal_arg(self):
        with self.assertRaises(
                TypeError,
                msg='accepting float namespace reference parameter'):
            nsr.get_parentns(42.0)
        with self.assertRaises(
                TypeError,
                msg='accepting None namespace reference parameter'):
            nsr.get_parentns(None)

    def test_owner_uid(self):
        # by path...
        self.assertIn(
            nsr.get_owner_uid(self.nspath('user')),
            (0, 65534), # ...covers containerized CI test
            'owner ID of root user namespace not root'
        )
        with open(self.nspath('user')) as nsref:
            # by file...
            self.assertEqual(
                nsr.get_owner_uid(nsref),
                0,
                'owner ID of root user namespace not root'
            )
            # by fd...
            self.assertEqual(
                nsr.get_owner_uid(nsref.fileno()),
                0,
                'owner ID of root user namespace not root'
            )

    def test_owner_uid_illegal_arg(self):
        with self.assertRaises(
                TypeError,
                msg='accepting float namespace reference parameter'):
            nsr.get_owner_uid(42.0)
        with self.assertRaises(
                TypeError,
                msg='accepting None namespace reference parameter'):
            nsr.get_owner_uid(None)
