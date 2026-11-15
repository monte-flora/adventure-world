"""
THE SHOP and THE BLACKSMITH'S REPAIRS, in Phase 2: spend gold, and sell what you don't need.

Prices and stock are in phase2/data/shop.json. Every shopkeeper has their own stock, kept in
game.shop_stock = {shopkeeper id: {item id: how many are left}} (plain data, so it saves by itself).
You get gold from quests, from gold coins in chests, and by selling things.

This file knows nothing about graphics. The shop screen is in phase2/draw_people.py.
"""

import json
import os

import rules

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "shop.json")

_data = None


def data():
    global _data
    if _data is None:
        with open(DATA_FILE, encoding="utf-8") as file:
            _data = json.load(file)
    return _data


def start_gold():
    return data().get("start_gold", 0)


def repair_price():
    return data()["repair_price"]


def buy_list(shopkeeper=None):
    """What a shopkeeper sells (a person from people.json, or None for everything)."""
    only = (shopkeeper or {}).get("sells")
    return [item for item in data()["buy"] if only is None or item["id"] in only]


def sell_list():
    return data()["sell"]


def stock_left(game, shop_id, item):
    """How many of item this shop still has (None: as many as you like)."""
    if item.get("stock") is None:
        return None
    stock = game.shop_stock.setdefault(shop_id, {})
    return stock.get(item["id"], item["stock"])


# ----- buying -----------------------------------------------------------------------------

def buy_problem(game, shop_id, item):
    """Why you can't buy this right now - or None if you can."""
    p = game.player
    left = stock_left(game, shop_id, item)
    if left == 0:
        return "Sold out!"
    if game.gold < item["price"]:
        return "You need %d gold (you have %d)." % (item["price"], game.gold)
    kind = item["id"]
    if kind == "food" and p.food >= p.max_food:
        return "Your pack is full of food."
    if kind == "arrows" and p.arrows >= p.max_arrows:
        return "You can't carry any more arrows."
    if kind == "bow" and p.has_bow:
        return "You already have a bow."
    if kind == "sword" and (p.sunfang or len(p.swords) >= rules.MAX_SWORDS):
        return "You can only carry %d swords." % rules.MAX_SWORDS
    if kind == "armor" and p.armor >= p.max_armor:
        return "Your armor is as good as new."
    return None


def buy(game, shop_id, item):
    """Buy one. Returns (True, what happened) or (False, why not)."""
    problem = buy_problem(game, shop_id, item)
    if problem:
        return False, problem
    p, kind = game.player, item["id"]
    game.gold -= item["price"]
    if kind == "food":
        p.food += 1
    elif kind == "arrows":
        p.arrows = min(p.max_arrows, p.arrows + rules.ARROWS_PER_BUNDLE)
    elif kind == "bow":
        p.has_bow = True
    elif kind == "sword":
        p.swords.append(rules.make_sword())
    elif kind == "armor":
        p.put_on_armor()
    left = stock_left(game, shop_id, item)
    if left is not None:
        game.shop_stock[shop_id][kind] = left - 1
    words = "You buy %s for %d gold." % (item["name"].lower(), item["price"])
    game.log(words, "loot")
    game.sound("pickup")
    return True, words


# ----- selling ----------------------------------------------------------------------------

def sell_problem(game, item):
    p, kind = game.player, item["id"]
    if kind == "wood" and p.wood < 1:
        return "You have no wood to sell."
    if kind == "food" and p.food < 1:
        return "You have no food to sell."
    if kind == "sword" and len(p.swords) < 2:
        return "Keep your sword! You can only sell a spare one."
    return None


def sell(game, item):
    problem = sell_problem(game, item)
    if problem:
        return False, problem
    p, kind = game.player, item["id"]
    if kind == "wood":
        p.wood -= 1
    elif kind == "food":
        p.food -= 1
    elif kind == "sword":
        p.swords.remove(min(p.swords, key=lambda s: s.durability))     # the one with the fewest hits left
    game.gold += item["price"]
    words = "You sell %s for %d gold." % (item["name"].lower(), item["price"])
    game.log(words, "loot")
    game.sound("pickup")
    return True, words


# ----- the blacksmith ---------------------------------------------------------------------

def most_worn(swords):
    return min(swords, key=lambda s: s.durability / s.max_durability)


def repair_problem(game):
    p = game.player
    worn = [s for s in p.swords if s.durability < s.max_durability]
    if not worn:
        return "Your swords are as good as new."
    if game.gold < repair_price():
        return "A repair costs %d gold (you have %d)." % (repair_price(), game.gold)
    return None


def repair(game):
    """The blacksmith mends your most worn sword. Returns (True/False, what happened)."""
    problem = repair_problem(game)
    if problem:
        return False, problem
    sword = most_worn(game.player.swords)
    sword.durability = sword.max_durability
    sword.chipped = False
    game.gold -= repair_price()
    words = "Clang, clang! Your sword is as good as new (%d hits). -%d gold" % (sword.durability, repair_price())
    game.log(words, "good")
    game.sound("clang")
    return True, words
