import unittest
import namespace_relations as nsr


class NsrTests(unittest.TestCase):

    def test_get_nstype(self):
        for ns_name, ns_type in (
            ('cgroup', nsr.CLONE_NEWCGROUP),
            ('ipc', nsr.CLONE_NEWIPC),
            ('mnt', nsr.CLONE_NEWNS),
            ('net', nsr.CLONE_NEWNET),
            ('pid', nsr.CLONE_NEWPID),
            ('user', nsr.CLONE_NEWUSER),
            ('uts', nsr.CLONE_NEWUTS)
        ):
            self.assertEqual(
                nsr.get_nstype('/proc/self/ns/%s' % ns_name),
                ns_type,
                'invalid namespace type returned '
                'for "%s" namespace' % ns_name
            )
