"""
THE STORY of Adventure World.

These are the story cards the game shows you. Change the words to tell the
story your own way! Each card has a title, the words, and which picture to
show with it. {name} turns into the name you typed on the title screen.

Pictures you can use: "king", "monsters", "sunfang", "portal", "hollow", "castle", "light"
"""

# The cards you see when a new game starts
INTRO = [
    ("The Shadow King",
     "Far away, in a dark world called Nightfall Hollow, lives the Shadow King. "
     "He hates the light. Every night he reaches through the old Portal and steals "
     "a little more of the light from our world.",
     "king"),
    ("The monsters come",
     "As the light fades, monsters creep out of the dark: Zombies, Skeletons, "
     "Ember Skulls and Spiders. Even the lakes have Sea Serpents now!",
     "monsters"),
    ("Sunfang",
     "The old stories say only one thing can beat him: Sunfang, a sword with a bite "
     "of pure sunlight. To forge it you need 3 diamonds. Find them, defeat 5 monsters "
     "to prove you're brave, and the Portal will open. Good luck, {name}!",
     "sunfang"),
]

# When you step through the open Portal
THROUGH_THE_PORTAL = [
    ("Nightfall Hollow",
     "{name} steps through the Portal... into Nightfall Hollow. Here it is always the "
     "last minute before night, and the sky never stops being dark purple.",
     "portal"),
    ("Find the castle",
     "Far away, the Shadow King's castle glows. Find it! The monsters here are shadow "
     "monsters: tougher than the ones back home. Rest at the glowing shrines - "
     "the monsters can't reach you there.",
     "hollow"),
]

# When you reach the castle gate with 3 diamonds
FORGE_SUNFANG = [
    ("The castle gate",
     "The castle gates are sealed shut with dark magic. But as {name} comes closer, "
     "the three diamonds in the pack begin to glow... brighter... and BRIGHTER!",
     "castle"),
    ("Forge Sunfang!",
     "It's time to forge Sunfang! Press each key as it appears, before its ring closes. "
     "Every strike of the hammer pulls the diamonds closer together.",
     "sunfang"),
]

# After Sunfang is forged
SUNFANG_DONE = [
    ("Sunfang is yours!",
     "With one last strike, the three diamonds melt together into a blade of pure "
     "sunlight. Sunfang never breaks, and it hits harder than any sword ever made.",
     "sunfang"),
]

# When the castle gates open (this is level 1's card, too)
AT_THE_CASTLE = [
    ("The gates open",
     "Sunfang's light touches the gates, and they creak open. Inside, torches flicker "
     "and shadow guards keep watch. The throne room is 5 levels away, and every level "
     "ends in a LOCKED door. Find the key or the lever to open it!",
     "castle"),
    ("Light shards",
     "Each level also hides a glowing light shard. Every one you find makes Sunfang "
     "glow brighter... and you'll need all the light you can get when you meet the Shadow King!",
     "sunfang"),
]

# The first time you reach each of the other castle levels (the Shadow King is watching you...)
LEVEL_2_CARD = [
    ("Level 2: The Great Hall",
     "A cold voice echoes through the hall: \"So, little light-bringer, you got past my moat. "
     "But my Great Hall has no key at all! Good luck finding my secret lever...\"",
     "king"),
]
LEVEL_3_CARD = [
    ("Level 3: The Dungeon",
     "\"Welcome to my dungeon, {name}!\" laughs the Shadow King. \"My jailer hid the key "
     "down in the tightest tunnel. Let's see you crawl!\"",
     "king"),
]
LEVEL_4_CARD = [
    ("Level 4: The Tower",
     "\"Still here?\" The Shadow King sounds angry now. \"My tower is so tall that nobody "
     "has ever climbed it. The lever is at the very top!\"",
     "king"),
]
LEVEL_5_CARD = [
    ("Level 5: The Battlements",
     "\"ENOUGH!\" roars the Shadow King. \"My guard captain has the key to my throne room, "
     "and ALL my guards are waiting for you on the battlements!\"",
     "king"),
]
CASTLE_LEVEL_CARDS = [AT_THE_CASTLE, LEVEL_2_CARD, LEVEL_3_CARD, LEVEL_4_CARD, LEVEL_5_CARD]

# The first time the guards knock you out in the castle
# When you run out of lives. It's not the end: you get new lives and keep everything you found!
OUT_OF_LIVES = [
    ("Out of lives!",
     "Game over... or is it? A real hero never gives up! {name} gets 3 new lives and keeps "
     "everything in the pack. Take a deep breath, eat some food, and try again!",
     "light"),
]

KNOCKED_OUT = [
    ("Knocked out!",
     "Everything goes dark... and {name} wakes up at the start of the level. The Shadow King's "
     "magic threw you back! But the guards you beat stay beaten, and the doors you opened stay "
     "open. Eat some food and try again!",
     "castle"),
]

# When you beat the Shadow King in the throne room: the end of the story!
THE_LIGHT_COMES_BACK = [
    ("The Shadow King falls",
     "With one last blaze of Sunfang, the Shadow King cracks like old ice... and bursts into "
     "a thousand sparks of light! His crown rolls across the floor, and the shadows run away.",
     "sunfang"),
    ("The light comes back",
     "All the light he ever stole pours out of the castle and back through the Portal. "
     "The sun rises over Nightfall Hollow for the very first time, and back home the days "
     "are long and bright again. You did it, {name}!",
     "light"),
]
