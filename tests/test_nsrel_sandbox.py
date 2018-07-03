import unittest
import namespace_relations as nsr
import subprocess
import os


class NsrTestsWithSandbox(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = subprocess.Popen([
            'unshare',
            '--user',  # create new user namespace
            '--map-root-user',
            '--net',
            'sleep', '1m'
        ], close_fds=True)

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.terminate()
        cls.sandbox.wait()

    def test_get_user(self):
        pid = NsrTestsWithSandbox.sandbox.pid
        userns_id = os.stat('/proc/%d/ns/user' % pid).st_ino
        with nsr.get_userns('/proc/%d/ns/net' % pid) as userns_f:
            netns_userns_id = os.fstat(userns_f.fileno()).st_ino
        self.assertEqual(
            netns_userns_id,
            userns_id
        )
