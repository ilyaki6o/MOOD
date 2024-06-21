"""Start client."""
import socket
import threading
from ..client import client as cl
import argparse

argparser = argparse.ArgumentParser()

argparser.add_argument("username", type=str, default='client1', help="Your username in game")
argparser.add_argument("--file", type=str, help="Comands file")
argparser.add_argument("--host", default='localhost', help="host addr")
argparser.add_argument("--port", type=int, default=1337, help="connection port")

args = argparser.parse_args()


name = args.username
host = args.host
port = args.port


def client():
    """Start client."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(f'login {name}\n'.encode())
        f = int(s.recv(2).rstrip().decode())
        if f:
            print(f'User {name} registered', end='\n\n')

            if args.file:
                with open(args.file, "r") as f:
                    cmd = cl.MUD(s, stdin=f, timeout=1)
                    cmd.prompt = ""
                    cmd.use_rawinput = False
                    tread = threading.Thread(target=cl.read_chat, args=[s, cmd]).start()
                    cmd.cmdloop()

            else:
                cmd = cl.MUD(s)
                tread = threading.Thread(target=cl.read_chat, args=[s, cmd]).start()
                cmd.cmdloop()
        else:
            print(f"User with name {name} already exists")
