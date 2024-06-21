import unittest
from unittest.mock import patch
import mood.client.__main__ as cli
from io import StringIO
import sys


class TestClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # pass
        sys.stdout = open('/dev/null', 'w')

    def test_1_down(self):
        with (patch('sys.stdin', StringIO("down")), patch('socket.socket') as sock,
                patch('mood.client.client.read_chat')):
            cli.client()
            self.assertEqual(sock.mock_calls[8].args[0], b'move 0 1\n')

    def test_2_left(self):
        with (patch('sys.stdin', StringIO("left")), patch('socket.socket') as sock,
                patch('mood.client.client.read_chat')):
            cli.client()
            self.assertEqual(sock.mock_calls[8].args[0], b'move -1 0\n')

    def test_3_addmon_daemon(self):
        cmd = 'addmon daemon hello "What a hell" coords 0 1 hp 100'
        with (patch('sys.stdin', StringIO(cmd)), patch('socket.socket') as sock,
                patch('mood.client.client.read_chat')):
            cli.client()
            self.assertEqual(sock.mock_calls[8].args[0], b"addmon daemon phrase 'What a hell' hp 100 coords 0 1\n")

    def test_4_addmon_cheese(self):
        cmd = 'addmon cheese hello "Papaya" coords 0 1 hp 15'
        with (patch('sys.stdin', StringIO(cmd)), patch('socket.socket') as sock,
                patch('mood.client.client.read_chat')):
            cli.client()
            self.assertEqual(sock.mock_calls[8].args[0], b"addmon cheese phrase 'Papaya' hp 15 coords 0 1\n")

    def test_5_unknown_monster(self):
        cmd = 'addmon petrovich hello "Vodka gde?" coords 0 1 hp 10000'
        with (patch('sys.stdin', StringIO(cmd)), patch('socket.socket'),
                patch('builtins.print') as res, patch('mood.client.client.read_chat')):
            cli.client()
            self.assertEqual(res.mock_calls[1].args[0], "Cannot add unknown monster")
