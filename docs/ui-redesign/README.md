# Phase 2: the new side panel and message box

Asked 2026-11-13: "re-design the right-hand side and the bottom... a more interactive, more intuitive
menu... the message box easier to read and more engaging", without overwhelming a young player.
Classic keeps its old panel (picture 17).

What changed, and why:

| Before | Now | Why |
| --- | --- | --- |
| A PACK list of 9 rows, most saying "none" | An icon for each thing you have, with a number | Only what you have is worth reading |
| "Defeat 5 monsters" (Classic's quest) and "Portal: closed" | A gold **NEXT** card: the main quest's step in a few words, an arrow and the steps, the 7 Light Stones filling in | One clear thing to do next |
| A grid of 12 keys, always | The 2-4 keys that work where you stand ("SPACE talk to Rosa"); every key is on the **H** page | Fewer words, and they're always true |
| 2 small yellow lines at the bottom | The newest message is big, with a picture, and glows for 5 seconds; older ones are small under it | You notice when something new is said |
| | Big news (quests, treasure) pops up over the map for 3.5 seconds | That's where you're looking |
| A small map | The same map with a gold pin for NEXT; **B** opens the big map with names | "Where do I go?" |
| | **L** opens the message log | Read what you missed |
| | Hold the mouse over anything for a tooltip; click the NEXT card (quests), the map, the message box | Find out what a thing is by pointing at it |

The pictures `take_screenshots.py` makes (with no window). Only `09-big-map-B.png` is kept in the repo; run the script to make the rest:

| Picture | What it shows |
| --- | --- |
| `01-new-game-home-meadow.png` | A new game: the welcome pops up as two toasts |
| `02-new-game-a-few-seconds-later.png` | The same, once the toasts are gone: the calm look |
| `03-next-to-a-person.png` | Next to Rosa: "SPACE talk to Rosa" lights up, NEXT says "right here!" |
| `04-quest-started-toast.png` | A new quest: a toast, the glowing message, the arrow and the pin |
| `05-mid-game-lots-of-items.png` | Mid-game: 9 things in the pack, powers, 2 Light Stones, hurt (E eat lights up) |
| `06-hover-tooltip-on-the-sword.png` | The mouse over the sword: what it is and how to get another |
| `07-loot-message-and-toast.png` | Treasure: a coin toast and the message |
| `08-level-up.png` | The LEVEL UP! card over the new panel |
| `09-big-map-B.png` | B: the big map |
| `10-message-log-L.png` | L: the message log |
| `11-every-key-H.png` | H: every key |
| `12-in-a-cave.png` | In a cave: NEXT says find the EXIT door, and every cave move is listed |
| `13-in-a-cave-hurt.png` | Hurt in a cave: a red message, and E eat on top |
| `14-nightfall-hollow.png` | Nightfall Hollow: the Sunfang list is in the NEXT card |
| `15-a-fight.png` | A fight on the map |
| `16-a-tip-points-at-the-food.png` | A tip bubble still points at the food |
| `17-classic-is-unchanged.png` | Classic: the old panel, as before |
