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
import tests.linuxnsrel
import subprocess
import os
import unittest
import time


class NsrTestsWithSandbox(tests.linuxnsrel.LxNsRelationsTests):

    # Only a single sandbox for all tests.
    sandbox = None  # type: subprocess.Popen

    @classmethod
    def setUpClass(cls):
        """Sets up a "sandbox" consisting of a sleeping cat in its
        own user namespace. No cats are being harmed during these
        tests. Only at the end, but don't tell anyone."""
        cls.sandbox = subprocess.Popen([
            'unshare',  # note that we don't fork!
            '--user',  # create new user namespace
            '--map-root-user',
            '--net',
            '/bin/cat'
        ], close_fds=True)
        # Now this is ugly ... unshare will need some time to do its
        # dirty work. If we just speed ahead then some tests may fail
        # later, because the sandboxed sleeping cat hasn't yet been
        # executed and we still see the unshare process instead. So,
        # wait and see for our sleeping cat to settle: only then we'll
        # see its user namespace change.
        userns_id = cls.nsid(cls.nspath('user'))
        while userns_id == cls.nsid(
                cls.nspath('user', cls.sandbox.pid)):
            time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        """Tears down the sandbox with the sleeping cat. It might be
        Schrödinger's Cat. Or it might not."""
        cls.sandbox.terminate()
        cls.sandbox.wait()

    @property
    def sandbox_pid(self):
        """Returns the PID of the sandbox, which is the sleeping cat."""
        return NsrTestsWithSandbox.sandbox.pid

    def test_get_user_sandbox(self):
        userns_id = self.nsid(self.nspath('user', self.sandbox_pid))
        with nsr.get_userns(self.nspath('net', self.sandbox_pid)) \
                as userns_f:
            netns_userns_id = self.file_nsid(userns_f)
        self.assertEqual(
            netns_userns_id, userns_id,
            'get_userns returning sandbox user namespace')

    def test_get_parent_user(self):
        root_userns_id = self.nsid(self.nspath('user'))
        with nsr.get_userns(self.nspath('net', self.sandbox_pid)) \
                as sandbox_userns_f:
            with nsr.get_parentns(sandbox_userns_f) as parent_userns_f:
                parent_userns_id = self.file_nsid(parent_userns_f)
        self.assertEqual(
            root_userns_id, parent_userns_id,
            'get_parentns returning root user namespace')

    def test_get_user_of_user(self):
        root_userns_id = self.nsid(self.nspath('user'))
        with nsr.get_userns(self.nspath('user', self.sandbox_pid)) \
                as root_userns_alias_f:
            root_userns_alias_id = self.file_nsid(root_userns_alias_f)
        self.assertEqual(
            root_userns_id,
            root_userns_alias_id,
            'owner of sandbox owner is root')
