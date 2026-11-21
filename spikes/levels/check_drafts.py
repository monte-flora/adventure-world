"""Run the cave robot (cave_solver.py) on the Wave A level drafts.

New letters from the proposed format (see docs/teen/levels/README.md) are swapped for
today's letters first, so today's robot can check them:  C (checkpoint) -> air.

    python spikes/levels/check_drafts.py docs/teen/levels/drafts/*.txt
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import cave_solver  # noqa: E402

NEW_TO_OLD = {"C": "."}


def today_format(text):
    head, rows = [], []
    for line in text.splitlines():
        (head if ":" in line and not rows else rows).append(line)
    rows = ["".join(NEW_TO_OLD.get(ch, ch) for ch in row) for row in rows]
    head = [h for h in head if h.split(":")[0] in ("theme", "name", "lava rises", "about")]
    return "\n".join(head + rows) + "\n"


if __name__ == "__main__":
    bad = 0
    for path in sys.argv[1:]:
        result = cave_solver.check(today_format(open(path).read()), time_limit=600)
        ok = result.get("exit") and result.get("diamond") is not False and all(c["ok"] for c in result["chests"])
        bad += not ok
        print(path, "OK" if ok else "STUCK", {k: result[k] for k in ("lever", "diamond", "exit", "stuck_at", "chests", "seconds") if k in result})
    sys.exit(1 if bad else 0)
