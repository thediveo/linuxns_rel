"""Discovers the available user namespaces and prints them in their
tree hierarchy to the console."""

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


from linuxns_rel import get_parentns, get_owner_uid, CLONE_NEWUSER, \
    CLONE_NEWPID
import psutil
import os
import pwd
import asciitree
import asciitree.traversal
from asciitree.drawing import BoxStyle, BOX_LIGHT
from asciitree.traversal import Traversal
from typing import cast, Dict, List, Optional, Tuple


class HierarchicalNamespaceIndex:
    """Index for hierarchical Linux kernel namespaces, specifically the
    PID and user hierarchical namespaces at this time."""

    def __init__(self, namespace_type: int) -> None:
        """Sets up a hierarchical namespace index by discovering the
        available namespaces of the specific namespace type.

        :param namespace_type: type of hierarchical namespace, either
          `linuxns_rel.CLONE_NEWUSER` or `linuxns_rel.CLONE_NEWPID`.
        """
        if namespace_type == CLONE_NEWUSER:
            self._nstypename = 'user'
        elif namespace_type == CLONE_NEWPID:
            self._nstypename = 'pid'
        else:
            raise ValueError('unsupported namespace type')
        # Dictionary of user/PID namespaces, indexed by their inode
        # numbers.
        self._index: Dict[int, 'HierarchicalNamespace'] = dict()
        # Dictionary of root namespace(s), indexed by their inode
        # numbers (again). Normally, this should only show a single
        # root, unless we have limited visibility.
        self._roots: Dict[int, 'HierarchicalNamespace'] = dict()
        self._discover_from_proc()
        self._discover_missing_parents()

    def print_tree(self) -> None:
        """"""

    def _discover_from_proc(self) -> None:
        """Discovers namespaces via `/proc/[PID]/ns/[TYPE]`."""
        # Never assume that this will locate *all* namespaces in the
        # hierarchy yet, but only those currently in use by
        # processes. In this first phase, we only collect namespaces,
        #  but don't bother with the parent-child relationships.
        for process in psutil.process_iter():
            try:
                ns_ref = '/proc/%d/ns/%s' % \
                         (process.pid, self._nstypename)
                with open(ns_ref) as nsf:
                    ns_id = os.stat(nsf.fileno()).st_ino
                    if ns_id not in self._index:
                        owner_uid = get_owner_uid(nsf)
                        self._index[ns_id] = HierarchicalNamespace(
                            ns_id, owner_uid, ns_ref)
            except PermissionError:
                pass

    def _discover_missing_parents(self) -> None:
        """"""
        # Next in phase two, we now discover the parent-child
        # relationships of the hierarchical namespaces discovered
        # during phase one. The unexpected surprise here is that we
        # may find parent namespaces that we didn't discover so far:
        # because these intermediate namespaces don't have any
        # process joined to them. But as these are hierarchical
        # namespaces you can't simply leave out an intermediate
        # namespace node. So we need to update the namespace index
        # while we iterate over a copy of it from phase one. This is
        # fine, as we recursively discover parent namespaces starting
        # from each namespace from phase one.
        for _, ns in self._index.copy().items():
            ns_ref = None
            try:
                ns_ref = open(ns.nsref)
                while ns_ref:
                    ns_id = os.stat(ns_ref.fileno()).st_ino
                    try:
                        parent_ns_ref = get_parentns(ns_ref)
                        parent_ns_id = os.stat(
                            parent_ns_ref.fileno()).st_ino
                        # Hoi! We might find out about parents we
                        # didn't know of so far from the process
                        # discovery phase. So we might need to add
                        # these newly found parents to our user
                        # namespace index.
                        if parent_ns_id not in self._index:
                            parent_uid = get_owner_uid(parent_ns_ref)
                            self._index[parent_ns_id] = \
                                HierarchicalNamespace(parent_ns_id,
                                                      parent_uid)
                        # Wire up our parent-child namespace
                        # relationship.
                        self._index[ns_id].parent = \
                            self._index[parent_ns_id]
                    except PermissionError:
                        # No more parent, or the parent is out of our
                        # scope.
                        parent_ns_ref = None
                        if ns_id not in self._roots:
                            self._roots[ns_id] = self._index[ns_id]
                    # Release the current user namespace file
                    # reference, and switch over to the parent's user
                    #  namespace file reference.
                    ns_ref.close()
                    ns_ref = parent_ns_ref
            finally:
                # Whatever has happened, make sure to *not* leak (or,
                # rather waste) the user namespace file reference.
                if ns_ref:
                    ns_ref.close()

    class HierarchicalNamespaceTraversal(Traversal):
        """Traverses a tree of user namespace objects."""

        def get_root(self, tree: [Dict[int, 'HierarchicalNamespace']]) \
                -> 'HierarchicalNamespace':
            """Return the root node of a tree. In case we get more
            than a single root of user namespaces, we return a "fake"
            ro(o)t instead, which then contains the list/tuple of
            user namespaces. """
            if len(tree) == 1:
                return next(iter(tree.values()))
            fake_root = HierarchicalNamespace(0, 0)
            fake_root.children = tree.values()
            return fake_root

        def get_children(self, node: 'HierarchicalNamespace') \
                -> List['HierarchicalNamespace']:
            """Returns the list of child user namespaces for a user
            namespace node."""
            return node.children

        def get_text(self, node: 'HierarchicalNamespace') -> str:
            """Returns the text for a user namespace node. It
            consists of the user namespace identifier (inode number).
            """
            if node.id:
                return 'user:[%d] owner %s (%d)' % (
                    node.id, pwd.getpwuid(node.uid).pw_name, node.uid)
            return '?'

    def render(self) -> None:
        """Renders an ASCII tree using our hierarchical namespace
        traversal object."""
        print(
            asciitree.LeftAligned(
                traverse=HierarchicalNamespaceIndex
                    .HierarchicalNamespaceTraversal(),
                draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=2)
            )(self._roots))


class HierarchicalNamespace:
    """A Linux user namespace, identified by its inode number, with
    the optional filesystem path where the user namespace can be
    referenced, at the hierarchical parent-child relations to other
    user namespaces."""

    def __init__(self, id: int, uid: int,
                 nsref: Optional[str] = None) -> None:
        """Represents a Linux user namespace, together with its
        hierarchical parent-child relationships.

        :param id: the unique identifier of this user namespace in
          form of a inode number.
        :param uid: the user ID "owning" this user namespace.
        :param nsref: a filesystem path reference to this user
          namespace, if known. Defaults to None, unless specified
          otherwise.
        """
        self.id = id
        self.nsref = nsref
        self.uid = uid
        self._parent: 'HierarchicalNamespace' = None
        self.children: List['HierarchicalNamespace'] = []

    @property
    def parent(self) -> 'HierarchicalNamespace':
        """Gets or sets the parent user namespace. Setting the parent
        will also add this user namespace to the children user
        namespaces of the parent user namespace.
        """
        return self._parent

    @parent.setter
    def parent(self, parent: 'HierarchicalNamespace') -> None:
        if not self._parent:
            self._parent = parent
            parent.children.append(self)


def main():
    """CLI to "lsuns"."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Show Linux user namespace tree.'
    )

    args = parser.parse_args()
    HierarchicalNamespaceIndex(CLONE_NEWUSER).render()


if __name__ == '__main__':
    main()
