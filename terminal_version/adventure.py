#!/usr/bin/env python3
"""
Adventure World - a terminal adventure game.

Run it from a terminal:

    python3 adventure.py
    python3 adventure.py --name Hero --seed 42

Goal: defeat monsters, mine diamonds, then step into the Portal to win.
Only the Python standard library is used - no installs needed.
"""

import argparse
import os
import random
import sys
import time

# ---------------------------------------------------------------------------
# Game settings - change these to make the game easier or harder!
# ---------------------------------------------------------------------------

# Tiles
FOREST = "Forest"
MINE = "Mine"
PORTAL = "Portal"
HOUSE = "House"

# Items
SWORD = "Sword"
PICKAXE = "Pickaxe"

GAME_MAP = [
    [HOUSE,  FOREST, FOREST, MINE,   FOREST, FOREST],
    [FOREST, FOREST, MINE,   FOREST, FOREST, MINE],
    [MINE,   MINE,   FOREST, MINE,   PORTAL, FOREST],
    [FOREST, FOREST, FOREST, MINE,   FOREST, FOREST],
    [FOREST, MINE,   FOREST, MINE,   FOREST, FOREST],
    [MINE,   FOREST, FOREST, FOREST, FOREST, MINE],
]
START_POS = (0, 0)  # the House

# Chance that something bad happens when you walk onto a tile.
TILE_DANGER = {FOREST: 0.2, MINE: 0.35, HOUSE: 0.0, PORTAL: 0.0}
HEAL_EVENT_CHANCE = 0.12

MONSTER_NAMES = ["Zombie", "Skeleton", "Creeper"]
NUM_MONSTERS = 8
MONSTERS_TO_DEFEAT = 5
DIAMONDS_NEEDED = 3

PLAYER_HEALTH = 10
MAX_SWORDS = 3
MAX_FOOD = 3
SWORD_DURABILITY = 3
PICKAXE_DURABILITY = 5
REACTION_LIMIT = 1.5  # seconds you get to press Enter when forging a sword

DIRECTIONS = {
    "u": (-1, 0, "up"),
    "d": (1, 0, "down"),
    "l": (0, -1, "left"),
    "r": (0, 1, "right"),
}
ALIASES = {"up": "u", "down": "d", "left": "l", "right": "r", "s": "w",
           "stay": "w", "wait": "w", "quit": "q", "help": "?", "h": "?"}

INJURIES = {
    FOREST: [
        "😖 You trip over a root and scrape your knee.",
        "🪵 A falling branch hits you on the shoulder.",
        "🐍 A snake slithers out and nips your ankle!",
    ],
    MINE: [
        "🪨 You stumble into a sharp rock.",
        "🔥 You walk too close to a patch of lava!",
        "🦇 A swarm of bats knocks you over!",
    ],
}
HEALS = [
    "💧 You find a fresh spring and take a drink.",
    "🍀 A calming breeze soothes your wounds.",
    "🦋 A glowing butterfly lands on you... you feel better.",
    "🌿 You crush some herbs and feel revitalized.",
]


class QuitGame(Exception):
    """Raised when the player quits (or input runs out)."""


# ---------------------------------------------------------------------------
# Screen: printing, asking questions, and clearing the terminal
# ---------------------------------------------------------------------------

class Screen:
    """Handles all input/output so the game logic stays simple.

    Everything said during a turn is remembered, so after the screen is
    cleared and the map redrawn, the player still sees what just happened.
    """

    MAX_LOG_LINES = 18

    def __init__(self, clear_screen=True):
        self.interactive = sys.stdin.isatty() and sys.stdout.isatty()
        self.clear_screen = clear_screen and self.interactive
        self.log = []

    def say(self, message=""):
        print(message)
        self.log.append(message)

    def pause(self, seconds):
        # Only add dramatic pauses when a real person is playing.
        if self.interactive:
            time.sleep(seconds)

    def ask(self, prompt):
        try:
            return input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raise QuitGame()

    def redraw(self, draw_function):
        if self.clear_screen:
            if os.name == "nt":
                os.system("cls")
            else:
                print("\033[2J\033[H", end="")
        draw_function()
        if self.clear_screen and self.log:
            print("── What happened ──")
            for line in self.log[-self.MAX_LOG_LINES:]:
                print(line)
            print()
        self.log = []

    def wait_for_enter_cue(self, delay):
        """Wait `delay` seconds. Returns True if Enter was pressed too early."""
        if not self.interactive:
            return False
        try:
            import select
            ready, _, _ = select.select([sys.stdin], [], [], delay)
            if ready:
                sys.stdin.readline()
                return True
            return False
        except (ImportError, OSError, ValueError):
            # select() doesn't work on Windows consoles - just wait.
            time.sleep(delay)
            return False


# ---------------------------------------------------------------------------
# Game objects
# ---------------------------------------------------------------------------

class Tool:
    """A tool (sword or pickaxe) that wears out as you use it."""

    def __init__(self, name, durability):
        self.name = name
        self.durability = durability

    def use(self):
        """Wear the tool down by 1. Returns True if it just broke."""
        self.durability -= 1
        return self.durability <= 0

    def __str__(self):
        return f"{self.name} (durability {self.durability})"


class Player:
    def __init__(self, name):
        self.name = name
        self.health = PLAYER_HEALTH
        self.max_health = PLAYER_HEALTH
        self.pos = START_POS
        self.swords = [Tool(SWORD, SWORD_DURABILITY)]
        self.pickaxe = Tool(PICKAXE, PICKAXE_DURABILITY - 1)
        self.food = 1
        self.diamonds = 0
        self.has_armor = False

    @property
    def is_alive(self):
        return self.health > 0

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def hurt(self, amount):
        self.health = max(0, self.health - amount)

    def status_line(self):
        pick = "yes" if self.pickaxe else "no"
        armor = "  🛡️ armor" if self.has_armor else ""
        return (f"❤️  {self.health}/{self.max_health}   ⚔️  swords {len(self.swords)}"
                f"   ⛏️  pickaxe {pick}   🍎 food {self.food}"
                f"   💎 diamonds {self.diamonds}{armor}")


class Monster:
    def __init__(self, pos):
        self.name = random.choice(MONSTER_NAMES)
        self.health = random.randint(6, 10)
        self.max_damage = 3
        self.pos = pos

    @property
    def is_alive(self):
        return self.health > 0


class Quest:
    def __init__(self, description, goal_count):
        self.description = description
        self.goal_count = goal_count
        self.progress = 0

    @property
    def completed(self):
        return self.progress >= self.goal_count

    def advance(self, say):
        """Add one to the quest. Returns True the moment it is completed."""
        if self.completed:
            return False
        self.progress += 1
        say(f"📝 Quest progress - {self.description}: {self.progress}/{self.goal_count}")
        if self.completed:
            say("🎉 Quest complete!")
            return True
        return False

    def __str__(self):
        mark = "✅" if self.completed else "❌"
        return f"{mark} {self.description} ({self.progress}/{self.goal_count})"


# ---------------------------------------------------------------------------
# The game itself
# ---------------------------------------------------------------------------

class Game:
    def __init__(self, player_name, screen):
        self.screen = screen
        self.say = screen.say
        self.map = [row[:] for row in GAME_MAP]
        self.rows = len(self.map)
        self.cols = len(self.map[0])
        self.player = Player(player_name)
        self.monsters = self.spawn_monsters(NUM_MONSTERS)
        self.monster_quest = Quest(f"Defeat {MONSTERS_TO_DEFEAT} monsters", MONSTERS_TO_DEFEAT)
        self.diamond_quest = Quest(f"Mine {DIAMONDS_NEEDED} diamonds", DIAMONDS_NEEDED)
        self.quests = [self.monster_quest, self.diamond_quest]
        self.turn = 1
        self.won = False
        self.quit = False

    # ----- map helpers -----------------------------------------------------

    def tile_at(self, pos):
        r, c = pos
        return self.map[r][c]

    @property
    def here(self):
        return self.tile_at(self.player.pos)

    def in_bounds(self, pos):
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, pos):
        r, c = pos
        spots = [(r + dr, c + dc) for dr, dc, _ in DIRECTIONS.values()]
        return [p for p in spots if self.in_bounds(p)]

    def spawn_monsters(self, count):
        open_tiles = [(r, c) for r in range(self.rows) for c in range(self.cols)
                      if self.map[r][c] in (FOREST, MINE)
                      and abs(r - START_POS[0]) + abs(c - START_POS[1]) > 1]
        return [Monster(random.choice(open_tiles)) for _ in range(count)]

    def monster_here(self):
        for monster in self.monsters:
            if monster.is_alive and monster.pos == self.player.pos:
                return monster
        return None

    # ----- drawing ---------------------------------------------------------

    def draw(self):
        print("═" * 60)
        print(f"  🌍 Adventure World          Turn {self.turn}")
        print("═" * 60)
        monster_spots = {m.pos for m in self.monsters if m.is_alive}
        for r in range(self.rows):
            line = "  "
            for c in range(self.cols):
                letter = self.map[r][c][0]
                if (r, c) == self.player.pos:
                    line += f"[🧍{letter}] "
                elif (r, c) in monster_spots:
                    line += f"[👹{letter}] "
                else:
                    line += f"[ {letter} ] "
            print(line)
        print("  🧍 you  👹 monster   F forest  M mine  H house  P portal\n")
        print("  " + self.player.status_line())
        for quest in self.quests:
            print(f"  📜 {quest}")
        print()

    def show_inventory(self):
        p = self.player
        print("\n" + "*" * 40)
        print(f"  {p.name}'s pack")
        print("-" * 40)
        for sword in p.swords:
            print(f"  ⚔️  {sword}")
        if not p.swords:
            print("  ⚔️  no swords (you'll have to use your fists!)")
        print(f"  ⛏️  {p.pickaxe if p.pickaxe else 'no pickaxe'}")
        print(f"  🍎 Food x{p.food} (max {MAX_FOOD})")
        print(f"  💎 Diamonds x{p.diamonds}")
        print(f"  🛡️  Armor: {'yes (+2 max health)' if p.has_armor else 'none'}")
        print(f"  ❤️  Health {p.health}/{p.max_health}")
        print("*" * 40 + "\n")

    def show_help(self):
        print(f"""
  HOW TO WIN: defeat {MONSTERS_TO_DEFEAT} monsters AND mine {DIAMONDS_NEEDED} diamonds,
  then walk into the Portal (P).

  Forest (F): search for food (f), craft a sword (c), craft a pickaxe (p)
  Mine   (M): dig for diamonds (m) - you need a pickaxe
  House  (H): rest to heal (z) - monsters can't get you here
  Anywhere : move (u/d/l/r), wait (w), eat (e), inventory (i), quit (q)

  Monsters wander around the map. Land on one and you have to fight!
  Swords and pickaxes wear out, so keep crafting new ones.
""")

    # ----- main loop -------------------------------------------------------

    def run(self):
        try:
            while self.player.is_alive and not self.won:
                self.screen.redraw(self.draw)
                moved = self.take_turn()
                self.end_of_turn(moved)
                self.turn += 1
        except QuitGame:
            self.quit = True
        self.show_ending()

    def take_turn(self):
        """Ask for an action until one uses up the turn. Returns True if the player moved."""
        while True:
            print(f"You are in the {self.here}.")
            print("  Move: u d l r   w=wait  e=eat  i=inventory  ?=help  q=quit")
            if self.here == FOREST:
                print("  Forest: f=search for food  c=craft sword  p=craft pickaxe")
            elif self.here == MINE:
                print("  Mine: m=dig for diamonds")
            elif self.here == HOUSE:
                print("  House: z=rest and heal")

            choice = self.screen.ask("> ")
            choice = ALIASES.get(choice, choice)

            if choice == "q":
                raise QuitGame()
            elif choice in DIRECTIONS:
                if self.move(choice):
                    return True
            elif choice == "w":
                self.say(f"{self.player.name} waits and listens...")
                return False
            elif choice == "e":
                self.eat()  # eating is a free action
            elif choice == "i":
                self.show_inventory()
            elif choice == "?":
                self.show_help()
            elif choice == "f" and self.here == FOREST:
                if self.search_for_food():
                    return False
            elif choice == "c" and self.here == FOREST:
                if self.craft_sword():
                    return False
            elif choice == "p" and self.here == FOREST:
                if self.craft_pickaxe():
                    return False
            elif choice == "m" and self.here == MINE:
                if self.dig():
                    return False
            elif choice == "z" and self.here == HOUSE:
                self.rest()
                return False
            else:
                print("❓ You can't do that here. Type ? for help.\n")

    def end_of_turn(self, moved):
        if self.won:
            return
        if moved:
            self.random_event()
        self.move_monsters()
        monster = self.monster_here()
        if monster and self.here != HOUSE and self.player.is_alive:
            self.battle(monster)

    # ----- actions ---------------------------------------------------------

    def move(self, key):
        dr, dc, word = DIRECTIONS[key]
        r, c = self.player.pos
        new_pos = (r + dr, c + dc)
        if not self.in_bounds(new_pos):
            print("🚫 You can't go that way - that's the edge of the world.\n")
            return False
        self.player.pos = new_pos
        self.say(f"{self.player.name} moves {word} into the {self.here}.")
        if self.here == HOUSE:
            self.say("🏠 You're safe at home. Monsters can't reach you here.")
        elif self.here == PORTAL:
            self.check_portal()
        return True

    def eat(self):
        p = self.player
        if p.food == 0:
            print("🚫 You have no food to eat!\n")
        elif p.health == p.max_health:
            print("😋 You're already at full health - save it for later.\n")
        else:
            p.food -= 1
            p.heal(3)
            print(f"🍎 You eat some food and recover 3 health. Health: {p.health}/{p.max_health}\n")

    def search_for_food(self):
        if self.player.food >= MAX_FOOD:
            print("🎒 Your pack is already full of food.\n")
            return False
        self.say("🌿 You search the forest for food...")
        self.screen.pause(0.8)
        if random.random() < 0.75:
            self.player.food += 1
            self.say(f"🫐 You find some wild berries! Food: {self.player.food}/{MAX_FOOD}")
        else:
            self.say("😞 You searched for a while but didn't find anything.")
        return True

    def craft_pickaxe(self):
        if self.player.pickaxe:
            print("⛏️  You already have a pickaxe.\n")
            return False
        self.say("🪵 You gather sticks and sharp stones...")
        self.screen.pause(0.8)
        self.player.pickaxe = Tool(PICKAXE, PICKAXE_DURABILITY)
        self.say("⛏️  You crafted a new pickaxe!")
        return True

    def craft_sword(self):
        if len(self.player.swords) >= MAX_SWORDS:
            print(f"⚔️  You can only carry {MAX_SWORDS} swords.\n")
            return False
        self.say("🪵 You find some branches and stones... time to forge a sword!")
        print("🔨 Press Enter the moment you see NOW! (not before!)")
        self.screen.pause(0.5)
        if self.screen.wait_for_enter_cue(random.uniform(1.5, 4.0)):
            self.say("💥 Too early! The blade cracks. Try again later.")
            return True
        print("NOW!")
        start = time.time()
        self.screen.ask("")
        reaction = time.time() - start
        if reaction < REACTION_LIMIT:
            self.player.swords.append(Tool(SWORD, SWORD_DURABILITY))
            self.say(f"⚔️  Success! You forged a sword in {reaction:.2f}s!")
        else:
            self.say(f"😓 Too slow ({reaction:.2f}s) - the metal cooled and the sword broke.")
        return True

    def dig(self):
        p = self.player
        if not p.pickaxe:
            print("🚫 You need a pickaxe. Craft one in the forest (p).\n")
            return False
        self.say("⛏️  You swing your pickaxe at the rock...")
        self.screen.pause(0.8)
        roll = random.random()
        if roll < 0.35:
            p.diamonds += 1
            self.say(f"💎 A diamond! You now have {p.diamonds}.")
            if self.diamond_quest.advance(self.say):
                self.say("🌀 You feel the Portal humming somewhere on the map...")
        elif roll < 0.55:
            p.hurt(1)
            self.say(f"🪨 Rocks tumble down on you! -1 health ({p.health}/{p.max_health})")
        else:
            self.say("🪨 Just plain stone this time.")
        if p.pickaxe.use():
            p.pickaxe = None
            self.say("💔 Your pickaxe breaks! Craft a new one in the forest.")
        return True

    def rest(self):
        p = self.player
        p.heal(4)
        self.say(f"😴 You take a nap at home. Health: {p.health}/{p.max_health}")

    def check_portal(self):
        if all(q.completed for q in self.quests):
            self.say("🌀✨ The Portal swirls open and pulls you through!")
            self.won = True
        else:
            needs = [q.description for q in self.quests if not q.completed]
            self.say("🌀 The Portal flickers but stays closed. You still need to:")
            for need in needs:
                self.say(f"   - {need}")

    # ----- world events ----------------------------------------------------

    def random_event(self):
        p = self.player
        danger = TILE_DANGER.get(self.here, 0)
        roll = random.random()
        if roll < danger:
            self.say(random.choice(INJURIES[self.here]))
            p.hurt(1)
            self.say(f"💔 You lose 1 health. ({p.health}/{p.max_health})")
        elif roll < danger + HEAL_EVENT_CHANCE and self.here in (FOREST, MINE):
            self.say(random.choice(HEALS))
            p.heal(1)
            self.say(f"❤️  You gain 1 health. ({p.health}/{p.max_health})")
            if not p.has_armor and random.random() < 0.3:
                p.has_armor = True
                p.max_health += 2
                p.heal(2)
                self.say("🛡️  You found armor! Your max health goes up by 2.")

    def move_monsters(self):
        for monster in self.monsters:
            if monster.is_alive and random.random() < 0.5:
                choices = [pos for pos in self.neighbors(monster.pos)
                           if self.tile_at(pos) != HOUSE]
                if choices:
                    monster.pos = random.choice(choices)

    def player_attack(self):
        """Returns the damage dealt to the monster."""
        p = self.player
        if not p.swords:
            self.say("👊 You have no sword, so you punch it! 1 damage.")
            return 1
        if random.random() >= 0.7:
            self.say("😬 You missed!")
            return 0
        damage = random.randint(2, 6)
        self.say(f"🗡️  Your sword strike does {damage} damage!")
        if p.swords[0].use():
            p.swords.pop(0)
            self.say(f"💔 Your sword breaks! Swords left: {len(p.swords)}")
        return damage

    def battle(self, monster):
        p = self.player
        self.say(f"\n⚠️  A wild {monster.name} appears!")
        while monster.is_alive and p.is_alive:
            print(f"   👹 {monster.name}: {monster.health} health    ❤️  You: {p.health}/{p.max_health}")
            action = self.screen.ask("   Attack (a), run (r), or eat (e)? ")
            if action == "a":
                monster.health -= self.player_attack()
            elif action == "r":
                self.flee(monster)
                return
            elif action == "e":
                self.eat()
            else:
                print("❓ You hesitate...")

            if monster.is_alive and random.random() < 0.5:
                damage = random.randint(1, monster.max_damage)
                p.hurt(damage)
                self.say(f"👹 The {monster.name} hits you for {damage} damage!")

        if not monster.is_alive:
            self.monsters.remove(monster)
            self.say(f"🎉 You defeated the {monster.name}!")
            if self.monster_quest.advance(self.say):
                p.heal(p.max_health)
                self.say("🏅 Reward: you are fully healed!")

    def flee(self, monster):
        p = self.player
        if random.random() < 0.5:
            damage = random.randint(1, 2)
            p.hurt(damage)
            self.say(f"😱 The {monster.name} swipes at you as you run! -{damage} health")
        p.pos = random.choice(self.neighbors(p.pos))
        self.say(f"🏃 You escape to the {self.here}.")

    # ----- ending ----------------------------------------------------------

    def show_ending(self):
        print()
        print("*" * 60)
        if self.won:
            print(f"  🏆 {self.player.name} escaped through the Portal in {self.turn} turns!")
            print("  You WIN! Thanks for playing Adventure World.")
        elif not self.player.is_alive:
            print("  💀 You have died from your wounds. Game over.")
            print(f"  You defeated {self.monster_quest.progress} monsters and "
                  f"found {self.player.diamonds} diamonds.")
        else:
            print("  Thanks for exploring! Come back soon.")
        print("*" * 60)


def main():
    parser = argparse.ArgumentParser(description="Adventure World")
    parser.add_argument("--name", help="your player's name")
    parser.add_argument("--seed", type=int, help="random seed (same seed = same game)")
    parser.add_argument("--no-clear", action="store_true", help="don't clear the screen each turn")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    screen = Screen(clear_screen=not args.no_clear)
    print("\n" + "*" * 60)
    print("*  Welcome to Adventure World!")
    print("*" * 60 + "\n")

    name = args.name
    if not name:
        try:
            name = screen.ask("Enter player name: ").title()
        except QuitGame:
            return
    name = name or "Adventurer"

    game = Game(name, screen)
    game.show_help()
    try:
        screen.ask("Press Enter to start your adventure...")
    except QuitGame:
        return
    game.run()


if __name__ == "__main__":
    main()
