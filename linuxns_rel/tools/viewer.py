"""Displays the SVG graph in a viewer window.

Due to security constraints, we're not able to run web browsers with
a (top-level) "data:" URL anymore. So we're using our own simple
Qt5-based SVG viewer, which we need to spawn as the original non-root
user -- otherwise Qt5 will refrain from working when tried to be run
as the root user.
"""

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


import os
import sys
import subprocess


def view(content: [str, bytes]) -> None:
    """Starts the SVG viewer and shows the specified content. The
    viewer always gets started as the original user in case the
    calling module is run with sudo.
    """
    cmd = []
    if 'SUDO_UID' in os.environ and 'SUDO_GID' in os.environ:
        cmd.extend([
            'sudo',
            '-E',  # allows us to keep the correct desktop env setup
            '-u', '#%s' % os.environ['SUDO_UID'],
            '-g', '#%s' % os.environ['SUDO_GID'],
            '--'
        ])
    cmd.extend([
        sys.executable,
        '-m', 'linuxns_rel.tools.viewer_impl',
        '-t', 'PID and user namespaces graph'
    ])
    viewer_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    if isinstance(content, str):
        viewer_process.communicate(content.encode('utf-8'))
    else:
        viewer_process.communicate(content)
    viewer_process.stdin.close()
