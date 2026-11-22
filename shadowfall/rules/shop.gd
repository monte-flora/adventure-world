class_name Shop
## Traders: buy with gold, sell sun ore. Wares and prices in rules/data/shop.json; a trader in
## people.json may sell only some ('sells'). Stock left lives in Game.flags["stock"]["trader:item"].


static func _data() -> Dictionary:
	return RulesData.get_file("shop")


static func _item(list: String, id: String) -> Dictionary:
	for it in _data().get(list, []):
		if it["id"] == id:
			return it
	return {}


## What this trader sells (all of shop.json's 'buy' list if they have no 'sells').
static func wares(trader: String) -> Array:
	var sells: Array = RulesData.person(trader).get("sells", [])
	return _data().get("buy", []).filter(func(it): return sells.is_empty() or it["id"] in sells)


## How many are left (-1: no end).
static func stock(trader: String, id: String) -> int:
	var it := _item("buy", id)
	if it.is_empty():
		return 0
	if it.get("stock") == null:
		return -1
	return int(Game.flags.get("stock", {}).get(trader + ":" + id, it["stock"]))


## Why you can't buy it, or "".
static func buy_problem(trader: String, id: String) -> String:
	var it := _item("buy", id)
	if it.is_empty() or wares(trader).filter(func(w): return w["id"] == id).is_empty():
		return "Not for sale here."
	if stock(trader, id) == 0:
		return "Sold out."
	var sigil: String = it.get("gives", {}).get("sigil", "")
	if sigil != "" and sigil in Sigils.owned():
		return "You have it already."
	if Game.gold < int(it["price"]):
		return "Not enough gold."
	return ""


static func buy(trader: String, id: String) -> bool:
	if buy_problem(trader, id) != "":
		return false
	var it := _item("buy", id)
	Vitals.take("gold", int(it["price"]))
	var left := stock(trader, id)
	if left > 0:
		if not Game.flags.has("stock"):
			Game.flags["stock"] = {}
		Game.flags["stock"][trader + ":" + id] = left - 1
	Quests.give_reward(it.get("gives", {}))
	return true


static func sell(id: String) -> bool:
	var it := _item("sell", id)
	if it.is_empty() or not Vitals.take(id, 1):
		return false
	Vitals.give("gold", int(it["price"]))
	return true


static func start_gold() -> int:
	return int(_data().get("start_gold", 0))
