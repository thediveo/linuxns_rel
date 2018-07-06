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

import unittest
import namespace_relations as nsr
import subprocess
import os


class NsrTestsWithSandbox(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = subprocess.Popen([
            'unshare',
            '--user',  # create new user namespace
            '--map-root-user',
            '--net',
            'sleep', '1m'
        ], close_fds=True)

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.terminate()
        cls.sandbox.wait()

    @property
    def sandbox_pid(self):
        return NsrTestsWithSandbox.sandbox.pid

    def test_get_user(self):
        userns_id = os.stat('/proc/%d/ns/user' % self.sandbox_pid).st_ino
        with nsr.get_userns('/proc/%d/ns/net' % self.sandbox_pid) as userns_f:
            netns_userns_id = os.fstat(userns_f.fileno()).st_ino
        self.assertEqual(
            netns_userns_id, userns_id,
            'get_userns() returning sandbox user namespace')

    def test_get_parent_user(self):
        root_userns_id = os.stat('/proc/self/ns/user').st_ino
        with nsr.get_userns('/proc/%d/ns/net' % self.sandbox_pid) as userns_f:
            with nsr.get_parentns(userns_f):
                parent_userns_id = os.fstat(userns_f.fileno()).st_ino
        self.assertEqual(
            root_userns_id, parent_userns_id,
            'get_parentns() returning root user namespace')

    def test_rootroot_use(self):
        nsr.get_parentns('/proc/self/ns/user')
