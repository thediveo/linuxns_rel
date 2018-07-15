"""Introspection of Linux kernel namespace relationships.

See also ioctl-ns(2):
http://man7.org/linux/man-pages/man2/ioctl_ns.2.html
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
from fcntl import ioctl
import struct
from typing import TextIO


# library/package semantic version
__version__ = '0.9.0'

# Linux namespace type constants; these are used with several of the
# namespace related functions, such as clone() in particular, but also
# setns(), unshare(), and the NS_GET_NSTYPE ioctl().
#
# https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/sched.h
CLONE_NEWNS = 0x00020000
CLONE_NEWCGROUP = 0x02000000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWUSER = 0x10000000
CLONE_NEWPID = 0x20000000
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
    if nstype in NAMESPACE_TYPE_NAMES:
        return NAMESPACE_TYPE_NAMES[nstype]
    raise ValueError('invalid namespace type value {i}/{h}'.format(
        i=nstype, h=hex(nstype)))


def get_nstype(nsref: [str, TextIO, int]) -> int:
    """Returns the type of namespace. The namespace can be referenced
    either via an open file, file descriptor, or path string."""
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
    path string."""
    return get_nsrel(nsref, NS_GET_USERNS)


def get_parentns(nsref: [str, TextIO, int]) -> TextIO:
    """Returns the parent namespace of a namespace, in form of a
    file object. The namespace parameter can be either an open file,
    file descriptor, or path string."""
    return get_nsrel(nsref, NS_GET_PARENT)


def get_owner_uid(usernsref: [str, TextIO, int]) -> int:
    """Returns the user ID of the owner of a user namespace, that is,
    the user ID of the process that created the user namespace. The
    user namespace parameter can be either an open file, file
    descriptor, or path string."""
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
