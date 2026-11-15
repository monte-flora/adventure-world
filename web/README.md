# The web-browser version

The same game, playing in a web page. [pygbag](https://github.com/pygame-web/pygbag) turns
it into WebAssembly, a kind of code every browser can run, so nobody has to install anything.

## Make it

```bash
pixi run -e web build-web
```

The first time, pixi downloads the web tools into their own environment, called `web`:
- **pygbag** makes the web page.
- **pygame-ce** is the pygame that runs in a browser.
- **ffmpeg** squeezes the music into small `.ogg` files.

The page ends up in `web/build/adventure/build/web/`, and `web.zip` next to it is ready
for itch.io. GitHub makes the same thing for every pull request and every merge into
`main`: open the run on the Actions tab, and download it under "Artifacts".

## Try it on your computer

```bash
python3 -m http.server 8123 --directory web/build/adventure/build/web
```

Then open **http://127.0.0.1:8123**. Use `127.0.0.1`, not `localhost`: on `localhost`,
pygbag looks for its own test server and gets stuck.

Click the page once (browsers only let a page make sound after a click), then play.
Shortcuts for play-testing go after a `?` in the address, joined with `&`:

| Address | What it does |
|---|---|
| `?castle` | start next to the Shadow King's castle |
| `?throne` | start in the throne room, fighting the Shadow King |
| `?mute` | start with the sound off |
| `?fps` | write how smoothly it runs to the browser's console, every 5 seconds |

## What's different in a browser

- **The music is made ahead of time.** On a computer the game makes its tunes with math
  while you play, in the background. A browser can't do background work like that, so
  `build_web.py` makes them into sound files first, and `Music.load_ready_made()` in
  `game.py` plays those.
- **The game gives the browser a turn after every picture.** That's the `await` in
  `main.py`. Everything else runs the same code as on a computer.
- **Esc goes back to the title screen**, because a web page can't close itself.
- **The cave editor isn't in the web version.** It saves files to a folder, and runs
  its robot as a separate program, and a web page can't do either.
- **It's about 5 times slower than on a computer**, because the browser is running
  Python inside WebAssembly. On a fast laptop every screen runs at a smooth 60 pictures
  a second. A fight takes about 8 ms of each picture's 16.7 ms.

## Putting it online

The repository is private, so the page needs a home of its own. itch.io is made for
games like this:
1. Make an itch.io account, then go to **Dashboard** > **Create new project**.
2. Set "Kind of project" to **HTML**.
3. Upload the zip, and tick **"This file will be played in the browser"**.
4. Set the viewport to about **1280 × 737** (the game's shape, small enough for a laptop),
   and tick **Fullscreen button**. Leave "Mobile friendly" off: the game needs a keyboard.
5. Under **Visibility & access**, pick **Restricted** and turn on a password. The page then
   isn't listed on itch.io or found by search engines. Send family the link and the password.
   Or leave the project as a **Draft**, and share the secret link shown at the top of its page.

People play it on a computer with a keyboard (laptop, desktop or Chromebook), in Chrome,
Edge or Firefox. They click the page once to let it make sound.

### New versions go up by themselves

GitHub can put every new version on your itch.io page, every time something is merged
into `main`. It uses butler, itch.io's own upload tool. To set it up, once:

1. **Make the itch.io page first** (the steps above). butler can only add to a page that
   already exists. Note its address: `https://YOURNAME.itch.io/GAME` means your page is
   `YOURNAME/GAME`.
2. **Get an itch.io API key**: itch.io > **Settings** > **API keys** > **Generate new API key**.
   It's like a password for uploading, so don't paste it anywhere else.
3. **Give it to GitHub as a secret.** In a terminal, run this, then paste the key when it asks:

       gh secret set BUTLER_API_KEY --repo monte-flora/adventure-world

   (Or on GitHub: **Settings** > **Secrets and variables** > **Actions** > **New repository secret**.)
4. **Tell GitHub which page**:

       gh variable set ITCH_GAME --repo monte-flora/adventure-world --body "YOURNAME/GAME"

5. **Run it once**: **Actions** > **Web version** > **Run workflow** (on `main`). The first upload
   goes into a new "html5" file on your page. On the page's edit screen, tick **"This file will
   be played in the browser"** for that file, and delete the zip you uploaded by hand. From
   then on, every merge into `main` updates it, and your family always get the newest version.

Until the key and the page are set, the job just builds the web page and skips the upload.
If the key ever ends up somewhere public, delete it on itch.io's API keys page, and make a new one.
