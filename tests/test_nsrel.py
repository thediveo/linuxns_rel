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
import linuxns_rel as nsr


class NsrTests(unittest.TestCase):

    def test_get_nstype(self):
        for ns_name, ns_type in (
            ('cgroup', nsr.CLONE_NEWCGROUP),
            ('ipc', nsr.CLONE_NEWIPC),
            ('mnt', nsr.CLONE_NEWNS),
            ('net', nsr.CLONE_NEWNET),
            ('pid', nsr.CLONE_NEWPID),
            ('user', nsr.CLONE_NEWUSER),
            ('uts', nsr.CLONE_NEWUTS)
        ):
            self.assertEqual(
                nsr.get_nstype('/proc/self/ns/%s' % ns_name),
                ns_type,
                'invalid namespace type returned '
                'for "%s" namespace' % ns_name
            )
