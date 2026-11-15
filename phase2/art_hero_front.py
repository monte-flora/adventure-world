"""The Hero knight at 32 x 32, seen from the front (Phase 2). His face shows under the open visor.

The rows are written without the empty squares on their right; `grid` fills them in and moves him
2 squares right, to the middle of the picture. His sword is not in the picture: the game puts it in his hand.
"""


def grid(rows):
    """32 rows of 32 letters from rows written short."""
    return [("." * 2 + row).ljust(32, ".") for row in rows]


_TOP = [                            # his plume, helmet, face, arms and chest (rows 0 to 24)
    "........kkkkk",
    "......kkxxrrRk",
    "....kkxxrrrrrRk",
    "...kxxrrrrrrrRRk",
    "...kxrrRkkkkkkkkkkkk",
    "...kxrRkiiiiaaaaaaaAk",
    "...kxRkiiiaaaaaaaaaaAk",
    "....kkiiaaaaaaaaaaaaAAk",
    ".....kiiakkkkkkkkkkaaAk",
    ".....kiakSsssaAsssdkaAk",
    ".....kiakSsksaAsksdkaAk",
    ".....kiakSskssssksdkaAk",
    ".....kiakS3sRssRs3dkaAk",
    ".....kaAkdsssRRsssdkAAk",
    ".....kaAkkkkkkkkkkkkAAk",
    "...kkkkkkAaaaaaaaaAkkkkkk",
    "..kiiiaakiiaaaaaaaAkiiaaAk",
    "..kiaaaAkiaaaaaaaaAkiaaaAk",
    "..kaaaAAkiaaaYYaaaAkaaaAAk",
    "...kkkkkkiaaYYYYaaAkkkkkk",
    "...kiaaAkiaaaYYaaaAkiaaAk",
    "...kiaaAkaaaaaaaaaAkiaaAk",
    "...kiaaAkNNNNYYNNNNkiaaAk",
    "...kaaAAkiaaaAiaaaAkaaAAk",
    "...kkkkkkiaaAAiaaAAkkkkkk",
]

# Standing still
FRONT_STAND = grid(_TOP + [
    "....kxrRkkkkkkkkkkkkrrRk",
    "....kxrRkiaaAkkiaaAkrrRk",
    "....kxRRkiaaAkkiaaAkrRRk",
    ".....kRRkAaaAkkAaaAkRRk",
    ".....kkkklleEkklleEkkkk",
    ".......kleeeEkkleeeEk",
    ".......kEEEEEkkEEEEEk",
])

# Walking down the map: one boot comes up, then the other
WALK_DOWN_1 = grid(_TOP + [
    "....kxrRkkkkkkkkkkkkrrRk",
    "....kxrRkAaaAkkiaaAkrrRk",
    "....kxRRklleEkkiaaAkrRRk",
    ".....kRkleeeEkkAaaAkRRk",
    ".....kkkEEEEEkklleEkkkk",
    "........kkkkkkkleeeEk",
    "..............kEEEEEk",
])

WALK_DOWN_2 = grid(_TOP + [
    "....kxrRkkkkkkkkkkkkrrRk",
    "....kxrRkiaaAkkAaaAkrrRk",
    "....kxRRkiaaAkklleEkrRRk",
    ".....kRRkAaaAkkleeeEkRk",
    ".....kkkklleEkkEEEEEkkk",
    ".......kleeeEkkkkkkkk",
    ".......kEEEEEk",
])
