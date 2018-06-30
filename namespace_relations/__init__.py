"""Introspection of Linux kernel namespace relationships.

See also ioctl-ns(2):
http://man7.org/linux/man-pages/man2/ioctl_ns.2.html
"""

import os
from fcntl import ioctl
from typing import TextIO

# Linux namespace type constants; these are used with several of the
# namespace related functions, such as clone() in particular, but also
# setns(), unshare(), and the NS_GET_NSTYPE ioctl().
# https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/sched.h
CLONE_NEWNS = 0x00020000
CLONE_NEWCGROUP = 0x02000000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWUSER = 0x10000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000

# Attention: these definitions holds only for the asm-generic platforms,
# such as x86.
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


# noinspection PyShadowingBuiltins
def _IOC(dir: int, type: int, nr: int, size: int) -> int:
    return ((dir << _IOC_DIRSHIFT) |
            (type << _IOC_TYPESHIFT) |
            (nr << _IOC_NRSHIFT) |
            (size << _IOC_SIZESHIFT))


# noinspection PyShadowingBuiltins
def _IO(type: int, nr: int) -> int:
    return _IOC(_IOC_NONE, type, nr, 0)


# https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/nsfs.h
NSIO = 0xb7

NS_GET_USERNS = _IO(NSIO, 0x1)
NS_GET_PARENT = _IO(NSIO, 0x2)
NS_GET_NSTYPE = _IO(NSIO, 0x3)


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
    return get_nsrel(nsref, NS_GET_USERNS)


def get_parentns(nsref: [str, TextIO, int]) -> TextIO:
    return get_nsrel(nsref, NS_GET_PARENT)

