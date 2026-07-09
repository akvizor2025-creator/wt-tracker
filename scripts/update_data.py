"""Fetches latest War Thunder news + changelog info and writes data/live.json.
Runs weekly via GitHub Actions (see .github/workflows/update.yml). Stdlib only."""
import json, re, os, datetime, urllib.request
from html.parser import HTMLParser

UA = {"User-Agent": "Mozilla/5.0 (compatible; WT-Update-Tracker/1.0; +https://github.com)"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self._href, self._buf = [], None, []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href, self._buf = dict(attrs).get("href"), []
    def handle_data(self, data):
        if self._href is not None:
            self._buf.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._buf).split())))
            self._href = None

def links(url):
    p = LinkCollector()
    p.feed(get(url))
    return p.links

news, seen = [], set()
for href, text in links("https://warthunder.com/en/news"):
    m = re.match(r"(?:https?://[^/]+)?(/en/news/(\d+)[^\s\"]*)", href or "")
    if m and len(text) >= 12 and m.group(2) not in seen:
        seen.add(m.group(2))
        news.append({"id": int(m.group(2)), "title": text,
                     "url": "https://warthunder.com" + m.group(1)})

latest = None
for href, text in links("https://warthunder.com/en/game/changelog"):
    m = re.search(r"/game/changelog/(?:current/)?(\d+)", href or "")
    if m:
        i = int(m.group(1))
        if not latest or i > latest["id"]:
            latest = {"id": i, "title": text or "Latest major update",
                      "url": "https://warthunder.com/en/game/changelog/current/%d" % i}

out = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "latest_changelog": latest, "news": news[:20]}
os.makedirs("data", exist_ok=True)
with open("data/live.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote data/live.json —", len(news), "news items; latest changelog:", latest)
