import time
import unittest
import mood.server.__main__ as server
import multiprocessing
import socket
import sys


def try_function(sock, method, message=""):
    sock.sendall(f"{method} {message}\n".encode())
    return sock.recv(4096).decode().strip()


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.stdout = open('/dev/null', 'w')
        cls.proc = multiprocessing.Process(target=server.server, args=[])
        cls.proc.start()
        time.sleep(0.05)
        cls.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.s.connect(("localhost", 1337))
        try_function(cls.s, "login", "client1")
        try_function(cls.s, "movemonsters", "off")
        try_function(cls.s, "locale", "ru_RU.UTF-8")

    def test_1_addmon(self):
        self.assertEqual(try_function(self.s, "addmon", "daemon phrase 'Hello' hp 15 coords 0 2"),
                         'Добавлен монстр daemon на (0, 2) говорящий: "Hello"')

    def test_2_move_hero(self):
        self.assertEqual(try_function(self.s, "move", "0 1"), 'Moved to (0, 1)')

    def test_3_encounter(self):
        self.assertEqual(try_function(self.s, "move", "0 1"),
                         r'''Moved to (0, 2)
 _______ 
< Hello >
 ------- 
   \         ,        ,
    \       /(        )`
     \      \ \___   / |
            /- _  `-/  '
           (/\/ \ \   /\
           / /   | `    \
           O O   ) /    |
           `-^--'`<     '
          (_.)  _  )   /
           `.___/`    /
             `-----' /
<----.     __ / __   \
<----|====O)))==) \) /====
<----'    `--' `.__,' \
             |        |
              \       /
        ______( (_  / \______
      ,'  ,-----'   |        \
      `--{__________)        \/''')

    def test_4_attack(self):
        self.assertEqual(try_function(self.s, "attack", "daemon spear"),
                         'Атакован daemon, урон 15 очков здоровья\ndaemon умер')

    @classmethod
    def tearDownClass(cls):
        cls.s.close()
        cls.proc.terminate()
