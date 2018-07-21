
import configparser
import shlex
import os
import subprocess
from typing import List, Optional


def _locate_desktop_file(desktopfile:str, paths:List[str]) \
        -> Optional[str]:
    for path in paths:
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if filename == desktopfile:
                    return os.path.join(root, filename)
    return None


def _default_webbrowser_cmd() -> Optional[str]:
    # (1) get the .desktop filename for the user's default web browser.
    default_wb_desktop_file = subprocess.check_output([
        'xdg-settings', 'get', 'default-web-browser'])\
        .decode('ascii').strip()
    # (2) locate this .desktop file according to XDG standards.
    paths = os.getenv(
        'XDG_DATA_HOME', os.environ['HOME'] + '/.local/share')\
        .split(':')
    paths.extend(os.getenv(
        'XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':'))
    wb_desktop_file_path = _locate_desktop_file(default_wb_desktop_file,
                                                paths)
    # (3) get Exec= inside [Desktop Entry]
    config = configparser.RawConfigParser()  # beware of "%u"...
    config.read(wb_desktop_file_path)
    return config['Desktop Entry']['Exec']


def default_webbrowser_open(url:str) -> None:
    cmd = []
    if 'SUDO_UID' in os.environ and 'SUDO_GID' in os.environ:
        cmd.extend([
            'sudo',
            '-u', '#%s' % os.environ['SUDO_UID'],
            '-g', '#%s' % os.environ['SUDO_GID'],
            '--'
        ])
    wb_cmd = _default_webbrowser_cmd().replace('%u', url)
    if wb_cmd:
        cmd.extend(shlex.split(wb_cmd))
        subprocess.Popen(cmd)


if __name__ == '__main__':
    default_webbrowser_open('data:,hi!')
