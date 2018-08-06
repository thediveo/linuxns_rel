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

"""Introspection of Linux kernel namespace relationships, such as
owning user namespace, parent namespace of a PID or user namespace,
the owner's user ID of a namespace, and some more.

* PyPi: https://pypi.org/project/linuxns-rel/ ... install with
  ``pip3 install linuxns-rel``
* GitHub project: https://github.com/TheDiveO/linuxns_rel
* ioctl-ns(2):
  http://man7.org/linux/man-pages/man2/ioctl_ns.2.html

CLI
---

This library comes with three simple CLI tools: ``lsuserns``,
``lspidns``, and ``graphns``. The first two tools simply pretty-print
the tree of Linux user (or PID) namespaces as can be discovered from
the visible running processes. And the third? We'll see...

To add some spice to the output, first open some user namespaces in
a separate terminal session (fails? see
`how to enable user_namespaces in the kernel? for unprivileged "unshare"
<https://unix.stackexchange.com/questions/303213/how-to-enable-user-namespaces-in-the-kernel-for-unprivileged-unshare>`_):

.. code-block:: console

    $ unshare -Ur unshare -Ur unshare -Ur unshare -Ur

.. code-block:: console

    $ lsuserns
    user:[4026531837] process "init" owner root (0)
    ├── user:[4026532465] process "firefox" owner foobar (1000)
    ├── user:[4026532523] process owner foobar (1000)
    │   └── user:[4026532524] process owner foobar (1000)
    │       └── user:[4026532525] process owner foobar (1000)
    │           └── user:[4026532526] process "bash" owner foobar (1000)
    ├── user:[4026532699] process "firefox" owner foobar (1000)
    ├── user:[4026532868] process "firefox" owner foobar (1000)
    └── user:[4026532467] process owner foobar (1000)

.. note:: You may want to use ``sudo lsuserns`` instead to really see
    *all* available user namespaces.

Bored of ASCII? Let's see a real graph (make sure that you've installed
``graphviz`` on your system, such as ``apt-get install graphviz``); this
example was taken using a freshly started chromium, the above user
namespace command, and finally also a firefox open.

.. code-block:: console

    $ sudo -E graphns

.. image:: _static/hns-graph.svg

.. note:: ``sudo -E`` ensures that you see all available user and PID
    namespaces, and also ensures that the graph viewer window correctly
    uses your desktop environment theme.

.. note:: All CLI tools are implemented in the same module
    :mod:`linuxns_rel.tools.lshierns`.


Examples
--------

Without much ado, let's try some examples. Simply import the
:mod:`linuxns_rel` package to discover Linux kernel namespace
relationships in Python.

>>> import linuxns_rel

Let's get the owner user namespace of your Python script, and then
print the user name of this owner.

>>> from pwd import getpwuid
>>> with linuxns_rel.get_userns('/proc/self/ns/net') as owner_ns:
...     owner_uid = linuxns_rel.get_owner_uid(owner_ns)
...     print('owning user:', getpwuid(owner_uid).pw_name)
owning user: root

Let's get the parent user namespace of the user namespace our Python
interpreter runs in.

>>> with linuxns_rel.get_parentns('/proc/self/ns/user') as parent_userns:
...     pass
Traceback (most recent call last):
  ...
PermissionError: [Errno 1] Operation not permitted

Now, here's the caveat: when we run this inside either the so-called
"root" user namespace so that there's no parent, or we don't have the
privileges to learn the parent, then Linux will in both cases return
an error, wrapped in a Python :exc:`PermissionError`.

All functions expecting a namespace reference, either accept:

* a string that represents a filesystem path, such as
  '/proc/self/ns/user'.
* a TextIO object, as returned by :func:`open` or some of the namespace
  relation functions, namely :func:`get_userns` and
  :func:`get_parentns`.
* a file descriptor or file number, such as returned by :func:`fileno`.

Please note that there is no way to get a filesystem path name returned
by :func:`get_userns` and :func:`get_parentns`: as Linux kernel
namespaces might even not be referenced in the filesystem and due to
the way \*nix filesystems work in general, there is no way to get back
a filesystem path name from an open file.

API
---
"""


import os
from fcntl import ioctl
import struct
from typing import TextIO


# library/package semantic version
__version__ = '1.0.3'

# Linux namespace type constants; these are used with several of the
# namespace related functions, such as clone() in particular, but also
# setns(), unshare(), and the NS_GET_NSTYPE ioctl().
#
# https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/sched.h
#: mount namespace type constant.
CLONE_NEWNS = 0x00020000
#: cgroup namespace type constant.
CLONE_NEWCGROUP = 0x02000000
#: uts (that is, \*nix timesharing system) namespace type constant.
CLONE_NEWUTS = 0x04000000
#: inter-process communication namespace type constant.
CLONE_NEWIPC = 0x08000000
#: user namespace type constant.
CLONE_NEWUSER = 0x10000000
#: PID namespace type constant.
CLONE_NEWPID = 0x20000000
#: network namespace type constant.
CLONE_NEWNET = 0x40000000

# Attention: the following definitions hold only for the "asm-generic"
# platforms, such as x86, arm, and others. Currently the only platforms
# having a different ioctl request field mapping are: alpha, mips,
# powerpc, and sparc.
#
# https://elixir.bootlin.com/linux/latest/source/include/uapi/asm-generic/ioctl.h
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT+_IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT+_IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT+_IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


# noinspection PyShadowingBuiltins,PyPep8Naming
def _IOC(dir: int, type: int, nr: int, size: int) -> int:
    """Returns an ioctl() request value, calculated for a specific ioctl
    call properties of parameter direction in/out, parameter size,
    type of ioctl, and command number.

    :param dir: direction of parameter, either `_IOC_NONE`, `_IOC_READ`,
      or `_IOC_WRITE`.
    :param type: ioctl command "type"; this is basically for grouping
      individual commands into groups, such as `NSIO` for
      namespace-related ioctl()s.
    :param nr: individual command inside the `type` group.
    :param size: size of parameter in bytes, from 0 to 2**14-1.
    :return: ioctl request number.
    """
    return ((dir << _IOC_DIRSHIFT) |
            (type << _IOC_TYPESHIFT) |
            (nr << _IOC_NRSHIFT) |
            (size << _IOC_SIZESHIFT))


# noinspection PyShadowingBuiltins,PyPep8Naming
def _IO(type: int, nr: int) -> int:
    return _IOC(_IOC_NONE, type, nr, 0)


# https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/nsfs.h
NSIO = 0xb7

# Returns a file descriptor that refers to an owning user namespace
NS_GET_USERNS = _IO(NSIO, 0x1)
# Returns a file descriptor that refers to a parent namespace
NS_GET_PARENT = _IO(NSIO, 0x2)
# Returns the type of namespace CLONE_NEW* value referred to by a file
# descriptor
NS_GET_NSTYPE = _IO(NSIO, 0x3)
# Get owner UID (in the caller's user namespace) for a user namespace
NS_GET_OWNER_UID = _IO(NSIO, 0x4)


# Dictionary mapping Linux namespace type constants to plain names.
# These are the same plain names as used by Linux namespace CLI tools,
# such as lsns(8).
NAMESPACE_TYPE_NAMES = {
    CLONE_NEWNS: 'mnt',
    CLONE_NEWCGROUP: 'cgroup',
    CLONE_NEWUTS: 'uts',
    CLONE_NEWIPC: 'ipc',
    CLONE_NEWUSER: 'user',
    CLONE_NEWPID: 'pid',
    CLONE_NEWNET: 'net'
}


def nstype_str(nstype: int) -> str:
    """Returns the type name for a certain namespace type. Typically,
    this function is used in  the context of :func:`get_nstype`, where
    all you got is a file, but not a path to (incorrectly) guess the
    type name of namespace from.

    >>> import linuxns_rel
    >>> linuxns_rel.nstype_str(
    ...     linuxns_rel.get_nstype('/proc/self/ns/net'))
    'net'

    So, what type of namespace does :func:`get_userns` return? As you
    might already guess: a user namespace. But let's check that:

    >>> linuxns_rel.nstype_str(
    ...     linuxns_rel.get_nstype(
    ...         linuxns_rel.get_userns('/proc/self/ns/net')))
    'user'
    """
    if nstype in NAMESPACE_TYPE_NAMES:
        return NAMESPACE_TYPE_NAMES[nstype]
    raise ValueError('invalid namespace type value {i}/{h}'.format(
        i=nstype, h=hex(nstype)))


def get_nstype(nsref: [str, TextIO, int]) -> int:
    """Returns the type of namespace. The namespace can be referenced
    either via an open file, file descriptor, or path string.

    The type returned is one of: :const:`CLONE_NEWNS`,
    :const:`CLONE_NEWCGROUP`, :const:`CLONE_NEWUTS`,
    :const:`CLONE_NEWIPC`, :const:`CLONE_NEWUSER`,
    :const:`CLONE_NEWPID`, :const:`CLONE_NEWNET`.

    >>> import linuxns_rel
    >>> linuxns_rel.get_nstype('/proc/self/ns/net') == linuxns_rel.CLONE_NEWNET
    True

    If you already have an open file referencing a Linux namespace, then
    you might use that directly:

    >>> with open('/proc/self/ns/net') as netns_f:
    ...     linuxns_rel.get_nstype(netns_f) == linuxns_rel.CLONE_NEWNET
    True
    """
    if isinstance(nsref, str):
        with open(nsref) as f:
            return ioctl(f.fileno(), NS_GET_NSTYPE)
    elif hasattr(nsref, 'fileno'):
        return ioctl(nsref.fileno(), NS_GET_NSTYPE)
    elif isinstance(nsref, int):
        return ioctl(nsref, NS_GET_NSTYPE)
    else:
        raise TypeError('namespace reference must be str, int or '
                        'TextIO, not {t}'.format(t=type(nsref)))


def get_nsrel(nsref: [str, TextIO, int], request: int) -> TextIO:
    """Returns a new namespace reference that is related to a namespace
    in the way specified by the `request` parameter. The namespace
    parameter can be either an open file, file descriptor, or path
    string."""
    if isinstance(nsref, str):
        with open(nsref) as f:
            userns = ioctl(f.fileno(), request)
    elif hasattr(nsref, 'fileno'):
        userns = ioctl(nsref.fileno(), request)
    elif isinstance(nsref, int):
        userns = ioctl(nsref, request)
    else:
        raise TypeError('namespace reference must be str, int or '
                        'TextIO, not {t}'.format(t=type(nsref)))
    return os.fdopen(userns, 'r')


def get_userns(nsref: [str, TextIO, int]) -> TextIO:
    """Returns the user namespace owning a namespace, in form of a
    file object referencing the owning user namespace. The owned
    namespace parameter can be either an open file, file descriptor, or
    path string.

    So let's get the owning user namespace of the PID namespace that
    our Python interpreter is using, and print it's user ID. It will be
    root (unless you are running this inside a sandbox which uses
    a different owning user namespace).

    >>> import linuxns_rel
    >>> with linuxns_rel.get_userns('/proc/self/ns/pid') as owning_userns_f:
    ...     linuxns_rel.get_owner_uid(owning_userns_f)
    0

    Please note that the owning user namespace of a user namespace is
    its parent user namespace, so :func:`get_userns` and
    :func:`get_parentns` are synonymous in this case.
    """
    return get_nsrel(nsref, NS_GET_USERNS)


def get_parentns(nsref: [str, TextIO, int]) -> TextIO:
    """Returns the parent namespace of a namespace, in form of a
    file object. The namespace parameter can be either an open file,
    file descriptor, or path string.

    You can then use the returned file object for further namespace
    operations, such as iterative calls to :func:`get_parentns`,
    specifying each time the file object returned by the previous call.

    However, it is **impossible** to retrieve a filesystem path,
    because Linux kernel namespaces might even not appear in the
    filesystem at all (such as "hidden" user namespaces without
    processes).

    At this time, only two out of the implemented Linux kernel
    namespaces are hierarchical: the PID and user namespaces. All other
    namespaces are flat, despite what you first might have expected.
    In the case of user namespaces, the parent of a user namespace is
    the same as the owning user namespace of a user namespace.

    In case you've reached the top of the hierarchical namespaces (at
    least from your point of view), then you'll get a
    :exc:`PermissionError`. This also happens when you have
    insufficient rights to further go up a namespace hierarchy.

    >>> import linuxns_rel
    >>> with linuxns_rel.get_parentns('/proc/self/ns/user') as parent_owner_f:
    ...     pass
    Traceback (most recent call last):
      ...
    PermissionError: [Errno 1] Operation not permitted

    When you ask for the parent namespace of a _flat_ namespace, you'll
    get an :exc:`OSError` instead:

    >>> with linuxns_rel.get_parentns('/proc/self/ns/uts') as parent_owner_f:
    ...     pass
    Traceback (most recent call last):
      ...
    OSError: [Errno 22] Invalid argument
    """
    return get_nsrel(nsref, NS_GET_PARENT)


def get_owner_uid(usernsref: [str, TextIO, int]) -> int:
    """Returns the user ID of the owner of a user namespace, that is,
    the user ID of the process that created the user namespace. The
    user namespace parameter can be either an open file, file
    descriptor, or path string.

    >>> import linuxns_rel
    >>> linuxns_rel.get_owner_uid('/proc/self/ns/user')
    0
    """
    # Ensure to catch most silent errors by initializing the user ID
    # return value with "MAXINT".
    uid = struct.pack('I', 2**32-42)
    if isinstance(usernsref, str):
        with open(usernsref) as f:
            uid = ioctl(f.fileno(), NS_GET_OWNER_UID, uid)
    elif hasattr(usernsref, 'fileno'):
        uid = ioctl(usernsref.fileno(), NS_GET_OWNER_UID, uid)
    elif isinstance(usernsref, int):
        uid = ioctl(usernsref, NS_GET_OWNER_UID, uid)
    else:
        raise TypeError('namespace reference must be str, int or '
                        'TextIO, not {t}'.format(t=type(usernsref)))
    return struct.unpack('I', uid)[0]
