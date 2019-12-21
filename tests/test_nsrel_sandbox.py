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

import subprocess
import time
import pytest

import linuxns_rel as nsr
from tests.linuxnsrel import LxNsRelationsTestHelper

@pytest.fixture(scope='class')
def sandbox(request):
    """Sets up a "sandbox" consisting of an infinite sleep in its own user
    and network namespaces."""
    # Oh, the joy of sysctl -w kernel.unprivileged_userns_clone=1
    request.cls.sandbox = subprocess.Popen([
        'unshare',  # note that we don't fork!
        '--user',  # create new user namespace
        '--map-root-user',
        '--net',
        '/bin/sleep', 'infinity'
    ], close_fds=True)
    # Now this is ugly ... unshare will need some time to do its dirty work.
    # If we just speed ahead then some tests may fail later, because the
    # sandboxed sleeping cat hasn't yet been executed and we still see the
    # unshare process instead. So, wait and see for our sleeping cat to
    # settle: only then we'll see its user namespace change.
    userns_id = request.cls.nsid(request.cls.nspath('user'))
    while userns_id == request.cls.nsid(
            request.cls.nspath('user', request.cls.sandbox.pid)):
        if request.cls.sandbox.poll():
            print('Skipping sandbox tests, is sysctl '
                  'kernel.unprivileged_userns_clone disabled?')
            request.cls.sandbox = None
            break
        time.sleep(0.1)
    yield
    # Tears down the sandbox.
    if request.cls.sandbox:
        request.cls.sandbox.terminate()
        request.cls.sandbox.wait()

@pytest.fixture(scope='function')
def sandboxed(request, sandbox): # pylint: disable=redefined-outer-name,unused-argument
    """Runs an individual test with a separate sandbox, if available; otherwise,
    skips the individual test."""
    if not getattr(request.cls, 'sandbox', None):
        pytest.skip('no user unshare sandbox available')


@pytest.mark.usefixtures('sandboxed')
class TestNsrWithSandbox(LxNsRelationsTestHelper):

    @property
    def sandbox_pid(self):
        """Returns the PID of the sandbox, which is the sleeping cat."""
        return type(self).sandbox.pid # type: ignore # pylint: disable=no-member

    def test_get_user_sandbox(self):
        userns_id = self.nsid(self.nspath('user', self.sandbox_pid))
        with nsr.get_userns(self.nspath('net', self.sandbox_pid)) \
                as userns_f:
            netns_userns_id = self.file_nsid(userns_f)
        assert netns_userns_id == userns_id, 'get_userns returning sandbox user namespace'

    def test_get_parent_user(self):
        root_userns_id = self.nsid(self.nspath('user'))
        with nsr.get_userns(self.nspath('net', self.sandbox_pid)) \
                as sandbox_userns_f:
            with nsr.get_parentns(sandbox_userns_f) as parent_userns_f:
                parent_userns_id = self.file_nsid(parent_userns_f)
        assert root_userns_id == parent_userns_id, 'get_parentns returning root user namespace'

    def test_get_user_of_user(self):
        root_userns_id = self.nsid(self.nspath('user'))
        with nsr.get_userns(self.nspath('user', self.sandbox_pid)) \
                as root_userns_alias_f:
            root_userns_alias_id = self.file_nsid(root_userns_alias_f)
        assert root_userns_id == root_userns_alias_id, 'owner of sandbox owner is root'
