"""Main functionality of server module."""
import io
import shlex
import asyncio
import cowsay
from ..common import custom_monsters
import random
import gettext
from pathlib import Path

_path = str(Path(__file__).parents[1])

LOCALES = {
    "ru_RU.UTF-8": gettext.translation("mood", _path, fallback=True),
    "en_US.UTF-8": gettext.NullTranslations(),
}


def ngettext(local, *args):
    """Redefine for choose locale."""
    return local.ngettext(*args)


def _(local, text):
    """Redefine for choose locale."""
    return local.gettext(text)


class Field:
    """Describe playing field."""

    def __init__(self):
        """Create playing field instance."""
        self.char_pos = {}

    def get_character(self, x: int, y: int):
        """
        Return character object by coordinates.

        :param x: horizontal coondinate
        :param y: vertical coordinate
        """
        return self.char_pos[(x, y)]

    def get_all_chars(self):
        """Return list of coondinates of all monsters on field."""
        return list(self.char_pos.keys())

    def check_position(self, x: int, y: int):
        """Check for the presence of a monster on cell with (x, y) coordinates."""
        return (x, y) in self.char_pos.keys()

    def set_character(self, x: int, y: int, other):
        """Insert monster on cell with (x, y) coordinates."""
        self.char_pos[(x, y)] = other

    def delete_character(self, x: int, y: int):
        """Remove monster on sell with (x, y) coordinates."""
        del self.char_pos[(x, y)]

    def encounter(self, x, y):
        """Call when monster and hero stend on same cell with (x, y) coordinates\
        and return cow saying monster catch phrase."""
        monster = self.get_character(x, y)
        name = monster.get_name()

        if name in cowsay.list_cows():
            return cowsay.cowsay(monster.get_phrase(), cow=name)
        elif name in custom_monsters:
            custom_cow = cowsay.read_dot_cow(io.StringIO(custom_monsters[name]))
            return cowsay.cowsay(monster.get_phrase(), cowfile=custom_cow)


class Character:
    """
    Base class of Mondter and Hero. Describe positions of all characters.

    :param field: playing field instance
    """

    x = 0
    y = 0

    def __init__(self, field: Field):
        """Set field on which character will play."""
        self.field = field

    def get_position(self):
        """Return cell coordinates on witch character stand."""
        return (self.x, self.y)

    def set_position(self, x: int, y: int):
        """Set character on cell with (x, y) coordinates."""
        self.x, self.y = x, y


class Hero(Character):
    """
    Describe hero characteristics.

    :param field: field on which hero will play
    :param name: user name
    """

    def __init__(self, field: Field, name: str):
        """Create hero with armory on cell with (0, 0) coordinates."""
        super().__init__(field)
        self.x = 0
        self.y = 0
        self.name = name
        self.weapon = "sword"
        self.armory = {"sword": 10,
                       "spear": 15,
                       "axe": 20}

    def choose_weapon(self, name):
        """
        Hero take weapon if it exist.

        :param neme: name of weapon, that hero take. Must exist.
        """
        if name in self.armory.keys():
            self.weapon = name
            return True
        return False

    def get_damage(self):
        """Return damage of choosed weapon."""
        return self.armory[self.weapon]

    def get_armory(self):
        """Return list of existing weapon names."""
        return self.armory.keys()

    def set_locale(self, name):
        """Set clients localization."""
        self.locale = LOCALES[name]

    def get_locale(self):
        """Return clients locale."""
        return self.locale


class Monster(Character):
    """
    Describe monster characteristics.

    :param x: horizontal coordinate of cell on which monster will stand
    :param y: vertical coordinate of cell on witch monster will stand
    :param name: monster name
    :param phrase: monster catch phrase
    :param hp: monster health points
    :param field: monster playing field
    """

    def __init__(self, x: int, y: int, name: str, phrase: str, hp: int, field: Field):
        """Create monster instance."""
        super().__init__(field)
        self.x = x
        self.y = y
        self.name = name
        self.phrase = phrase
        self.hp = hp
        self.field.set_character(self.x, self.y, self)

    def get_phrase(self):
        """Return monster catch phrase."""
        return self.phrase

    def get_name(self):
        """Return monster name."""
        return self.name

    def set_hp(self, new_hp: int):
        """
        Set monster new hp value.

        :param new_hp: monster new hp value
        """
        self.hp = new_hp

    def get_hp(self):
        """Return monster hp."""
        return self.hp


clients = {}
desk = Field()
task = None


async def roaming_monster():
    """Replace monster on one cell in random direction."""
    while True:
        monsters = desk.get_all_chars()

        if not monsters:
            await asyncio.sleep(10)
            continue

        await asyncio.sleep(30)

        while True:
            x, y = random.choice(monsters)
            if desk.check_position(x, y):
                monster = desk.get_character(x, y)
                a, b = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                x_new = (x + a) % 10
                y_new = (y + b) % 10

                if not desk.check_position(x_new, y_new):
                    break

        desk.set_character(x_new, y_new, monster)
        desk.delete_character(x, y)
        direction = ""

        match (a, b):
            case (0, -1): direction = "up"
            case (0, 1): direction = "down"
            case (1, 0): direction = "right"
            case (-1, 0): direction = "left"

        for el in clients.values():
            await el.put(f'{monster.get_name()} moved one cell {direction}')

        for char in clients.keys():
            if char.get_position() == (x_new, y_new):
                msg = desk.encounter(x_new, y_new)
                await clients[char].put(msg)


async def move(a, b, hero):
    """
    Move hero one cell.

    :param a: value that is added to coordinate x
    :param b: value that is added to coordinate y
    :param hero: moved hero
    """
    x, y = hero.get_position()
    x = (x + int(a)) % 10
    y = (y + int(b)) % 10
    hero.set_position(x, y)

    await clients[hero].put(f"Moved to ({x}, {y})")

    if desk.check_position(x, y):
        msg = desk.encounter(x, y)
        await clients[hero].put(msg)


async def addmon(name, phrase, hp, x, y, hero, me):
    """
    Add monster on field.

    :param name: monster name
    :param phrase: monster catch phrase
    :param hp: monster hp
    :param x: monster horizontal coordinate
    :param y: monster vertical coordinate
    :param hero: hero instance that add monster
    :param me: hero name
    """
    x, y = int(x), int(y)
    hp = int(hp)

    flag = desk.check_position(x, y)

    Monster(x, y, name, phrase, hp, desk)
    await clients[hero].put(
            _(hero.get_locale(), 'Added monster {} to ({}, {}) saying: "{}"').format(name, x, y, phrase))

    for cli, el in clients.items():
        if el is not clients[hero]:
            await el.put(ngettext(cli.get_locale(), 'User {} added monster {} with {} hp',
                                  'User {} added monster {} with {} hps', hp).format(me, name, hp))

    if flag:
        await clients[hero].put(_(hero.get_locale(), 'Replaced the old monster'))


async def attack(name, weapon, me, hero):
    """
    Hero attacks monster on cell, that he staying.

    :param name: monster name
    :param weamon: weapon name with which hero will attack
    :param me: hero name
    :param hero: hero instance
    """
    x, y = hero.get_position()

    if desk.check_position(x, y)\
            and (monster := desk.get_character(x, y)).get_name() == name:
        hero.choose_weapon(weapon)
        damage = hero.get_damage() if monster.get_hp() >= hero.get_damage()\
            else monster.get_hp()
        monster.set_hp(monster.get_hp() - damage)
        await clients[hero].put(ngettext(hero.get_locale(), "Attacked {}, damage {} hp",
                                         "Attacked {}, damage {} hps", damage).format(monster.get_name(), damage))

        if monster.get_hp() == 0:
            await clients[hero].put(_(hero.get_locale(), "{} died").format(monster.get_name()))
            desk.delete_character(x, y)
        else:
            await clients[hero].put(ngettext(hero.get_locale(), "{} now has {} hp",
                                             "{} now has {} hps", monster.get_hp()).format(monster.get_name(),
                                                                                           monster.get_hp()))

        for cli, el in clients.items():
            if el is not clients[hero]:
                tmp1 = ngettext(cli.get_locale(), "User {} attacked monster {} with {}, damage {} hp",
                                "User {} attacked monster {} with {}, damage {} hps",
                                damage).format(me, name, weapon, damage)
                tmp2 = "\n" + ngettext(cli.get_locale(), "{} now has {} hp",
                                       "{} now has {} hps", monster.get_hp()).format(name, monster.get_hp())\
                    if monster.get_hp() != 0 else "\n" + _(cli.get_locale(), "{} died").format(name)
                await el.put(tmp1 + tmp2)
    else:
        await clients[hero].put(_(hero.get_locale(), "No {} here").format(name))


async def roaming_monster_switch(flag, task):
    """Turn random mosters movements on/off."""
    match flag:
        case "on":
            try:
                task.cancel()
                await asyncio.sleep(0)
            except Exception:
                pass

            print("movemonsters on")

            task = asyncio.create_task(roaming_monster())
            await asyncio.sleep(0)
        case "off":
            print("movemonsters off")
            task.cancel()
            await asyncio.sleep(0)


async def mud(reader, writer):
    """
    Handle of messages from players.

    :param reader: Represents a reader object that provides APIs to read data from the IO stream
    :param writer: Represents a writer object that provides APIs to write data to the IO stream
    """
    log_in = asyncio.create_task(reader.readline())
    log_res = await log_in
    res_arr = log_res.decode().strip().split()
    me = ''

    match res_arr:
        case ["login", name]:
            if name in clients:
                writer.write(f'{0}\n'.encode())
                await writer.drain()
                reader.feed_eof()
                await reader.read()
            else:
                me = name
                writer.write(f'{1}\n'.encode())
                print(f"log in user: {me}")

    hero = Hero(desk, me)
    hero.set_locale("en_US.UTF-8")
    clients[hero] = asyncio.Queue()
    send = asyncio.create_task(reader.readline())
    receive = asyncio.create_task(clients[hero].get())

    if me:
        for cli, el in clients.items():
            if el is not clients[hero]:
                await el.put(_(cli.get_locale(), "User {} connected").format(me))

    while not reader.at_eof():
        done, pending = await asyncio.wait([send, receive], return_when=asyncio.FIRST_COMPLETED)

        for q in done:
            if q is send:
                send = asyncio.create_task(reader.readline())
                text = q.result().decode().strip()

                match shlex.split(text):
                    case ["move", a, b]:
                        await move(a, b, hero)
                    case ["addmon", name, "phrase", phrase, "hp", hp, "coords", x, y]:
                        await addmon(name, phrase, hp, x, y, hero, me)
                    case ["attack", name, weapon]:
                        await attack(name, weapon, me, hero)
                    case ["quit"]:
                        reader.feed_eof()
                        await reader.read()
                        break
                    case ["sayall", text]:
                        for el in clients.values():
                            if el is not clients[hero]:
                                await el.put(f"{me}: {text}")
                    case ["movemonsters", flag]:
                        await roaming_monster_switch(flag, task)

                        for el in clients.values():
                            await el.put(f"Moving monsters: {flag}")
                    case ["locale", name]:
                        if name not in LOCALES.keys():
                            hero.set_locale("en_US.UTF-8")
                            await clients[hero].put(_(hero.get_locale(), "Locale {} does not exist").format(name))
                        else:
                            hero.set_locale(name)
                            await clients[hero].put(_(hero.get_locale(), "Set up locale: {}".format(name)))
                    case _:
                        print(text)
            elif q is receive:
                res = q.result()

                while not clients[hero].empty():
                    res += '\n' + await clients[hero].get()

                receive = asyncio.create_task(clients[hero].get())
                writer.write((res).encode())
                await writer.drain()

    send.cancel()
    receive.cancel()

    if me:
        print(f"{me} disconnected")
        for cli, el in clients.items():
            if el is not clients[hero]:
                await el.put(_(cli.get_locale(), "{} disconnected").format(me))

    del clients[hero]
    writer.close()
    await writer.wait_closed()
