# WT Update Tracker

A self-updating War Thunder patch tracker. New vehicles with pics + armament details,
before/after remodel sliders, sort/filter, live BR lookups, and an auto-refreshing news feed.

## Setup (one time, ~5 minutes)

1. Create a free account at github.com (if you don't have one).
2. Click **+** (top right) → **New repository** → name it `wt-tracker` → set **Public** → Create.
3. On the repo page: **uploading an existing file** link → drag ALL files/folders from this
   zip in (index.html, README.md, data/, scripts/, .github/) → **Commit changes**.
   - If the .github folder won't drag in, create the file manually: **Add file → Create new file**,
     type `.github/workflows/update.yml` as the name, paste the contents of that file.
4. **Settings → Pages** → under "Branch" pick `main` and `/ (root)` → Save.
5. **Actions** tab → enable workflows → open "Weekly WT data refresh" → **Run workflow** (first run).

Your tracker is now live at: `https://YOURNAME.github.io/wt-tracker/`
Add that URL as an Opera Speed Dial tile.

## How it stays updated (no computer needed)

- GitHub's servers run the refresh script twice a week (Mon & Thu 12:00 UTC),
  updating the news feed and the "newer update detected" banner.
- The page itself also live-checks warthunder.com and the community vehicles API
  every time you open it.
- When a new major update drops, the banner tells you — ask Claude to rebuild the
  vehicle cards for the new patch, then replace index.html in the repo (Edit → paste → Commit).

Unofficial fan tool. Data & images © Gaijin Entertainment, fetched from warthunder.com. Not affiliated with Gaijin.
