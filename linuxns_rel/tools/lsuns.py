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


from linuxns_rel import get_parentns, get_owner_uid
import psutil
import os
import pwd
import asciitree
import asciitree.traversal
from asciitree.drawing import BoxStyle, BOX_LIGHT
from typing import cast, Dict, List, Optional, Tuple


class UserNS:
    """A Linux user namespace, identified by its inode number, with
    the optional filesystem path where the user namespace can be
    referenced, at the hierarchical parent-child relations to other
    user namespaces."""

    def __init__(self, id: int, uid: int,
                 nsref: Optional[str]=None) -> None:
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
        self._parent: 'UserNS' = None
        self.children: List['UserNS'] = []

    @property
    def parent(self) -> 'UserNS':
        """Gets or sets the parent user namespace. Setting the parent
        will also add this user namespace to the children user
        namespaces of the parent user namespace.
        """
        return self._parent

    @parent.setter
    def parent(self, parent: 'UserNS') -> None:
        if not self._parent:
            self._parent = parent
            parent.children.append(self)


def lsuns() -> None:
    """Prints all discoverable user namespaces in a tree hierarchy on
    standard output."""

    # Dictionary of user namespaces, indexed by their inode numbers.
    userns_index: Dict[int, UserNS] = dict()
    # Dictionary of root user namespace(s), indexed by their inode
    # numbers (again). Normally, this should only show a single root,
    # unless we have limited visibility.
    root_userns: Dict[int, UserNS] = dict()

    # Never assume that this will locate *all* user namespaces,
    # but only those currently in use by processes. In this first
    # phase, we only collect user namespaces, but don't bother with
    # the parent-child relationships.
    for process in psutil.process_iter():
        try:
            userns_ref = '/proc/%d/ns/user' % process.pid
            with open(userns_ref) as f_userns:
                userns_id = os.stat(f_userns.fileno()).st_ino
                if userns_id not in userns_index:
                    owner_uid = get_owner_uid(f_userns)
                    userns_index[userns_id] = UserNS(
                        userns_id, owner_uid, userns_ref)
        except PermissionError:
            pass

    # Next in phase two, we now discover the parent-child
    # relationships of the user namespaces discovered during phase
    # one. The unexpected surprise here is that we may find parent
    # user namespaces that we didn't discover so far: because these
    # intermediate user namespaces don't have any process joined to
    # them. So we need to update the user namespace index while we
    # iterate over a copy of it from phase one. This is fine,
    # as we recursively discover parent user namespaces starting from
    # each user namespace from phase one.
    for _, userns in userns_index.copy().items():
        userns_ref = None
        try:
            userns_ref = open(userns.nsref)
            while userns_ref:
                userns_id = os.stat(userns_ref.fileno()).st_ino
                try:
                    parent_userns_ref = get_parentns(userns_ref)
                    parent_userns_id = os.stat(
                        parent_userns_ref.fileno()).st_ino
                    # Hoi! We might find out about parents we didn't
                    # know of so far from the process discovery
                    # phase. So we might need to add these newly
                    # found parents to our user namespace index.
                    if parent_userns_id not in userns_index:
                        parent_uid = get_owner_uid(parent_userns_ref)
                        userns_index[parent_userns_id] = UserNS(
                            parent_userns_id, parent_uid)
                    # Wire up our parent-child user namespace
                    # relationship.
                    userns_index[userns_id].parent = \
                        userns_index[parent_userns_id]
                except PermissionError:
                    # No more parent, or the parent is out of our
                    # scope.
                    parent_userns_ref = None
                    if userns_id not in root_userns:
                        root_userns[userns_id] = userns_index[userns_id]
                # Release the current user namespace file reference,
                # and switch over to the parent's user namespace file
                # reference.
                userns_ref.close()
                userns_ref = parent_userns_ref
        finally:
            # Whatever has happened, make sure to *not* leak (or,
            # rather waste) the user namespace file reference.
            if userns_ref:
                userns_ref.close()

    class UserNSTraversal(asciitree.traversal.Traversal):
        """Traverses a tree of user namespace UserNS objects."""

        def get_root(self, tree: [Dict[int, UserNS]]) -> UserNS:
            """Return the root node of a tree. In case we get more
            than a single root of user namespaces, we return a "fake"
            ro(o)t instead, which then contains the list/tuple of
            user namespaces. """
            if len(tree) == 1:
                return next(iter(tree.values()))
            fake_root = UserNS(0, 0)
            fake_root.children = tree.values()
            return fake_root

        def get_children(self, node: UserNS) -> List[UserNS]:
            """Returns the list of child user namespaces for a user
            namespace node."""
            return node.children

        def get_text(self, node: UserNS) -> str:
            """Returns the text for a user namespace node. It
            consists of the user namespace identifier (inode number).
            """
            if node.id:
                return 'user:[%d] owner %s (%d)' % (
                    node.id, pwd.getpwuid(node.uid).pw_name, node.uid)
            return '?'

    # render an ASCII tree using our user namespace traversal object...
    print(
        asciitree.LeftAligned(
            traverse=UserNSTraversal(),
            draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=2)
        )(root_userns))


def main():
    """CLI to "lsuns"."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Show Linux user namespace tree.'
    )

    args = parser.parse_args()
    lsuns()


if __name__ == '__main__':
    main()
