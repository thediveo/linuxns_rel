# Linux Kernel Namespace Relations

> **NOTE:** Python 3.6+ supported only

This Python package allows discovering the following Linux Kernel
namespace relationships and properties:

- the _owning_ user namespace of another Linux kernel namespace.
- the _parent_ namespace of either a user or a PID namespace.
- type of a Linux kernel namespace: user, PID, network, ...
- owner user ID of a user namespace.

See also [ioctl() operations for Linux namespaces](http://man7.org/linux/man-pages/man2/ioctl_ns.2.html)
for more background information of the namespace operations exposed by
this Python library.


# Installation

```bash
$ pip3 install linuxns-rel
```

# CLI Examples

```bash
$ lsuns 
```

may yield something like this, a pretty hierarchy of Linux kernel user
namespaces:

```
user:[4026531837] owner root (0)
 ├── user:[4026532696] owner foobar (1000)
 ├── user:[4026532638] owner foobar (1000)
 ├── user:[4026532582] owner foobar (1000)
 │   └── user:[4026532639] owner foobar (1000)
 │       └── user:[4026532640] owner foobar (1000)
 │           └── user:[4026532641] owner foobar (1000)
 ├── user:[4026532466] owner foobar (1000)
 │   └── user:[4026532464] owner foobar (1000)
 ├── user:[4026532523] owner foobar (1000)
 └── user:[4026532583] owner foobar (1000)
```

This is the command used in another terminal session to create some
more hierarchical user namespaces:

```bash
$ unshare -Ur unshare -Ur unshare -Ur unshare -Ur
```

# API Examples

(..._to be added_)
