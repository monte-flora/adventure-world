"""
DIALOGUE for Phase 2: what people say, page by page, and the choices you get.

A person's "talk" in phase2/data/people.json is a set of NODES. Talking starts at "start".

    "talk": {
        "start": [                                         a list: the first one whose "if" is true
            {"if": ["quest_new:farmer_wood"],
             "say": ["Hello, {name}!", "Could you bring me 10 wood?"],     one page each
             "choices": [{"text": "Sure!", "do": ["start_quest:farmer_wood"], "go": "thanks"},
                         {"text": "Not now."}]},
            {"say": ["Nice day, isn't it?"]}
        ],
        "thanks": {"say": ["Thank you!"]}
    }

- "say": the pages. {name}, {gold} and the other words in people.words() get filled in.
- "if": conditions that must all be true (people.CONDITIONS says which there are). "not:..." flips one.
- "do": effects, done when the node starts (people.EFFECTS): start a quest, give gold...
- "choices": shown after the last page. A choice can have "if", "do" and "go" (the next node).
  A choice with no "go" ends the talk.
- "next": the node after the last page, if there are no choices. No "next": the talk ends.

This file knows nothing about graphics. The pictures are in phase2/draw_people.py.
"""

TYPE_SPEED = 45          # letters a second the typewriter types


class _Words(dict):
    def __missing__(self, key):          # a {word} we don't know stays as it is
        return "{" + key + "}"


class Conversation:
    """One talk with one person. `check(condition)` and `run(effect)` come from people.py."""

    def __init__(self, person, check, run, words=None):
        self.person = person
        self.nodes = person.get("talk", {})
        self.check = check
        self.run = run
        self.words = words or {}
        self.done = False
        self.then = None              # what opens after the talk: "shop", "forge"... (an effect sets it)
        self.go("start")

    # ----- moving through the nodes ---------------------------------------------------------

    def passes(self, conditions):
        if isinstance(conditions, str):
            conditions = [conditions]
        return all(self.check(c) for c in conditions or [])

    def pick(self, name):
        """The node called name (the first variant whose "if" is true), or None."""
        node = self.nodes.get(name)
        variants = node if isinstance(node, list) else [node] if node else []
        for variant in variants:
            if self.passes(variant.get("if")):
                return variant
        return None

    def go(self, name):
        node = self.pick(name) if name else None
        if node is None:
            self.end()
            return
        self.node = node
        self.page = 0
        self.typed = 0.0
        self.choice = 0
        for effect in node.get("do", []):
            self.run(effect, self)
        if self.done:                 # an effect ended the talk (it opened the shop...)
            return
        if not self.pages:            # a node with nothing to say: straight on
            self.after_last_page()

    def end(self):
        self.done = True

    # ----- what's showing -----------------------------------------------------------------

    @property
    def pages(self):
        return self.node.get("say", [])

    @property
    def text(self):
        """The whole page that's showing, with {name} and the rest filled in."""
        if self.done or not self.pages:
            return ""
        return self.fill(self.pages[self.page])

    def fill(self, text):
        """Fill in {name}, {gold}... in some words (a page, or a choice)."""
        words = self.words() if callable(self.words) else self.words
        return text.format_map(_Words(words))

    @property
    def shown(self):
        """As much of the page as the typewriter has typed so far."""
        return self.text[:int(self.typed)]

    @property
    def typing(self):
        return int(self.typed) < len(self.text)

    @property
    def last_page(self):
        return self.page >= len(self.pages) - 1

    @property
    def choices(self):
        """The choices you can pick right now (only once the last page is all typed)."""
        if self.done or self.typing or not self.last_page:
            return []
        return [c for c in self.node.get("choices", []) if self.passes(c.get("if"))]

    # ----- the keys -------------------------------------------------------------------------

    def update(self, dt):
        if not self.done:
            self.typed = min(len(self.text), self.typed + TYPE_SPEED * dt)

    def press(self):
        """ENTER or SPACE: finish typing, or the next page, or pick the highlighted choice."""
        if self.done:
            return
        if self.typing:
            self.typed = len(self.text)
        elif self.choices:
            self.choose(self.choice)
        elif not self.last_page:
            self.page += 1
            self.typed = 0.0
        else:
            self.after_last_page()

    def move(self, way):
        """UP (-1) or DOWN (+1) moves the highlight over the choices."""
        if self.choices:
            self.choice = (self.choice + way) % len(self.choices)

    def choose(self, i):
        choices = self.choices
        if not 0 <= i < len(choices):
            return
        picked = choices[i]
        for effect in picked.get("do", []):
            self.run(effect, self)
        if not self.done:
            self.go(picked.get("go"))

    def after_last_page(self):
        if self.node.get("choices"):
            if not self.choices:      # every choice is hidden: nothing to pick, so it ends
                self.end()
            return
        self.go(self.node.get("next"))
