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

from namespace_relations import get_parentns, get_owner_uid
import psutil
import os
import pwd
import asciitree
import asciitree.traversal
from asciitree.drawing import BoxStyle, BOX_LIGHT
from typing import cast, Dict, List, Optional, Tuple


class UserNS:

    def __init__(self, id: int, nsref: Optional[str]=None,
                 uid: Optional[int]=None) -> None:
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


userns_index: Dict[int, UserNS] = dict()
root_userns: Dict[int, UserNS] = dict()


# Never assume that this will locate *all* user namespaces, but only
# those currently in use by processes. In this first phase, we only
# collect user namespaces, but don't bother with the parent-child
# relationships.
for process in psutil.process_iter():
    try:
        userns_ref = '/proc/%d/ns/user' % process.pid
        with open(userns_ref) as f_userns:
            userns_id = os.stat(f_userns.fileno()).st_ino
            if userns_id not in userns_index:
                owner_uid = get_owner_uid(f_userns)
                userns_index[userns_id] = UserNS(
                    userns_id, userns_ref, owner_uid)
    except PermissionError:
        pass

# Next in phase two, we now discover the parent-child relationships
# of the user namespaces discovered during phase one. The unexpected
# surprise here is that we may find parent user namespaces that we
# didn't discover so far: because these intermediate user namespaces
# don't have any process joined to them. So we need to update the
# user namespace index while we iterate over a copy of it from phase
# one. This is fine, as we recursively discover parent user namespaces
# starting from each user namespace from phase one.
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
                # Hoi! We might find out about parents we didn't know
                # of so far from the process discovery phase. So we
                # might need to add these newly found parents to our
                # user namespace index.
                if parent_userns_id not in userns_index:
                    parent_uid = get_owner_uid(parent_userns_ref)
                    userns_index[parent_userns_id] = UserNS(
                        parent_userns_id, uid=parent_uid)
                # Wire up our parent-child user namespace relationship.
                userns_index[userns_id].parent = \
                    userns_index[parent_userns_id]
            except PermissionError:
                # No more parent, or the parent is out of our scope.
                parent_userns_ref = None
                if userns_id not in root_userns:
                    root_userns[userns_id] = userns_index[userns_id]
            # Release the current user namespace file reference, and
            # switch over to the parent's user namespace file reference.
            userns_ref.close()
            userns_ref = parent_userns_ref
    finally:
        # Whatever has happened, make sure to not leak user namespace
        # file references.
        if userns_ref:
            userns_ref.close()


class UserNSTraversal(asciitree.traversal.Traversal):
    """Traverses a tree of user namespace UserNS objects."""

    def get_root(self, tree: [UserNS, Dict[int, UserNS], List[UserNS],
                              Tuple[UserNS]]) -> UserNS:
        """Return the root node of a tree. In case we get a list or
        tuple of user namespaces instead of a single user namespace, we
        return a "fake" ro(o)t instead, which then contains the
        list/tuple of user namespaces."""
        if isinstance(tree, (list, tuple)):
            if len(tree) == 1:
                return tree[0]
            fake_root = UserNS(0)
            fake_root.children = tree
            return fake_root
        elif isinstance(tree, dict):
            if len(tree) == 1:
                return next(iter(tree.values()))
            fake_root = UserNS(0)
            fake_root.children = tree.values()
            return fake_root
        return cast(UserNS, tree)

    def get_children(self, node: UserNS) -> List[UserNS]:
        """Returns the list of child user namespaces for a user
        namespace node."""
        return node.children

    def get_text(self, node: UserNS) -> str:
        """Returns the text for a user namespace node. It consists of
        the user namespace identifier (inode number)."""
        if node.id:
            return 'user:[%d] owner %s (%d)' % (
                node.id, pwd.getpwuid(node.uid).pw_name, node.uid)
        return '?'


# render an ASCII tree using our user namespace traverser...
print(
    asciitree.LeftAligned(
        traverse=UserNSTraversal(),
        draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=2)
    )(root_userns))
