"""Main functionality of client module."""
import cowsay
from ..common import custom_monsters
import shlex
import cmd
import readline
import time
import webbrowser
from pathlib import Path

armory = ["sword", "spear", "axe"]

doc_path = str(Path(__file__).parents[1] / 'docs/build/html/index.html')


def read_chat(sock, cmd):
    """
    Listen server and pring all messages reveived from it.

    :param sock: Listening socket
    :param cmd: Command line instance
    """
    while True:
        try:
            msg = sock.recv(4096).rstrip().decode()
            print(f"\n{msg}\n{cmd.prompt}{readline.get_line_buffer()}", end="", flush=True)
        except Exception:
            print("Dead ^(")
            return


def move_hero(direction: str, cmd_socket):
    """
    Move hero one cell.

    :param direction: movement direction
    :param cmd_socket: socket to communicate with server
    """
    x, y = 0, 0
    match direction:
        case "up":
            x, y = 0, -1
        case "down":
            x, y = 0, 1
        case "left":
            x, y = -1, 0
        case "right":
            x, y = 1, 0

    cmd_socket.sendall(f"move {x} {y}\n".encode())


def addmon(options: str, cmd_socket):
    """
    Add monster on field.

    :param options: name, catch phrase, hp, coordinates of added monster
    :param cmd_socket: socket to communicate with server
    """
    opt = shlex.split(options)
    name = opt[0]
    opt = opt[1:]

    if len(opt) != 7:
        print('Invalid arguments')
        return

    if (name not in cowsay.list_cows()) and \
            (name not in custom_monsters):
        print('Cannot add unknown monster')
        return

    while opt:
        cnt = 0

        match opt:
            case ['hello', param, *tmp]:
                phrase = param
                cnt = 2
            case ['hp', param, *tmp]:
                try:
                    hp = int(param)
                except Exception:
                    break

                if (hp <= 0):
                    break

                cnt = 2
            case ['coords', p1, p2, *tmp]:
                try:
                    x, y = int(p1), int(p2)
                except Exception:
                    break

                if (x >= 10 or x < 0) or (y >= 10 or y < 0):
                    break

                cnt = 3
            case _:
                break

        opt = opt[cnt:]
    else:
        cmd_socket.sendall(f"addmon {name} phrase '{phrase}' hp {hp} coords {x} {y}\n".encode())
        return

    print('Invalid arguments')


def attack(options: str, cmd_socket):
    """
    Hero attacks monster in his cell.

    :param options: monster name, hero weapon
    :param cmd_socket: socket to communicate with server
    """
    if not options:
        print("Invalid arguments")
        return

    args = shlex.split(options)
    name = args[0]
    args = args[1:]
    weapon = "sword"

    if args:
        if args[0] == "with":
            if args[1] not in armory:
                print("Unknown weapon")
                return
            else:
                weapon = args[1]
        else:
            print("Invalid arguments")
            return

    cmd_socket.sendall(f'attack {name} {weapon}\n'.encode())


class MUD(cmd.Cmd):
    """
    Class for command line interpretation.

    :param s: socket to communicate with server
    :param timeout: make timeout between read cmdline from cmdfile
    """

    prompt = '~~> '
    intro = "<<< Welcome to Python-MUD 0.1 >>>\nType help or ? to list commands.\n"

    def __init__(self, s, timeout=0, *args, **kwargs):
        """Create command line instance."""
        super().__init__(*args, **kwargs)

        self.cmd_socket = s
        self.cmd_timeout = timeout

        if self.cmd_timeout != 0:
            self.cmd_socket.sendall("movemonsters off\n".encode())

    def precmd(self, line):
        """
        Make timeout between execute cmdline from cmdfile.

        :param line: executable cmd line
        """
        time.sleep(self.cmd_timeout)
        return super().precmd(line)

    # cmd settings
    def do_EOF(self, args):
        """Initiate socket closure."""
        print('\n')
        self.cmd_socket.sendall("quit\n".encode())
        return True

    # move hero
    def do_up(self, args):
        """Move the hero up one cell."""
        move_hero("up", self.cmd_socket)

    def do_down(self, args):
        """Move the hero down one cell."""
        move_hero("down", self.cmd_socket)

    def do_left(self, args):
        """Move the hero left one cell."""
        move_hero("left", self.cmd_socket)

    def do_right(self, args):
        """Move the hero right one cell."""
        move_hero("right", self.cmd_socket)

    # attack monsters
    def do_attack(self, args):
        """Hero attack monster on current cell."""
        attack(args, self.cmd_socket)

    def help_attack(self):
        """User documentation of attack function."""
        print("attack <name_str> {with <weapon_name>} - Hero attacks monster with name\
                == <name_str> on current cell")
        print("\n{with <weapon_name>} - choose weapon (default 'sword': damage 10 hp)")

    def complete_attack(self, text, line, begidx, endidx):
        """Complete monster name and weapon for attack function."""
        line = shlex.split(line)
        res = cowsay.list_cows() + list(custom_monsters.keys())

        if line[-1] == "with" or line[-2] == "with":
            return [i for i in armory if i.startswith(text)]
        elif line[-1] == "attack" or line[-2] == "attack":
            return [i for i in res if i.startswith(text)]

    # add new monster on field
    def do_addmon(self, args):
        """Add monster on field."""
        addmon(args, self.cmd_socket)

    def help_addmon(self):
        """User documentation of addmon function."""
        print("addmon <name> [hello <hello_string>] [hp <value>] [coords <x> <y>]")
        print("\n<name> - name of monster")
        print("[hello <hello_string>] - phrase that monster say on meeting with hero")
        print("[hp <value>] - monster hp (must be integer and above zero)")
        print("[coords <x> <y>] - coords cell on field, where monster\
                will stand (if there is already a monster on the cell, then replaces it)")
        print("\t<x> <y> must be integer in [0, 9]")

    # sey all players
    def do_sayall(self, args):
        """
        Send message for all MUD users.

        :param args: message to send
        """
        self.cmd_socket.sendall(f"sayall {args}\n".encode())

    def do_movemonsters(self, args):
        """Turn on/off random monsters movemets."""
        self.cmd_socket.sendall(f"movemonsters {args}\n".encode())

    def do_locale(self, args):
        """
        Set localization for messages that you will see.

        Available locales: ru_RU.UTF-8, en_US.UTF-8.

        :param args: name of locale
        """
        self.cmd_socket.sendall(f"locale {args}\n".encode())

    def do_documentation(self, args):
        """Open generated documentation."""
        webbrowser.open(doc_path)
