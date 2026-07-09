"""Fetches latest War Thunder news + changelog + vehicle BRs, writes data/live.json.
Runs twice weekly via GitHub Actions. Stdlib only."""
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

# ---------- news + changelog ----------
news, seen = [], set()
try:
    for href, text in links("https://warthunder.com/en/news"):
        m = re.match(r"(?:https?://[^/]+)?(/en/news/(\d+)[^\s\"]*)", href or "")
        if m and len(text) >= 12 and m.group(2) not in seen:
            seen.add(m.group(2))
            news.append({"id": int(m.group(2)), "title": text,
                         "url": "https://warthunder.com" + m.group(1)})
except Exception as e:
    print("news fetch failed:", e)

latest = None
try:
    for href, text in links("https://warthunder.com/en/game/changelog"):
        m = re.search(r"/game/changelog/(?:current/)?(\d+)", href or "")
        if m:
            i = int(m.group(1))
            if not latest or i > latest["id"]:
                latest = {"id": i, "title": text or "Latest major update",
                          "url": "https://warthunder.com/en/game/changelog/current/%d" % i}
except Exception as e:
    print("changelog fetch failed:", e)

# ---------- vehicle BRs from community datamine API ----------
# The API has no text search; page through the full list and match identifiers.
API = "https://wtvehiclesapi.duckdns.org/api/vehicles?limit=200&page=%d"
def norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def branch_of(vt):
    vt = (vt or "").lower()
    if "helicopter" in vt: return "heli"
    if any(k in vt for k in ("ship", "boat", "cruiser", "destroyer", "frigate",
                             "battleship", "barge", "naval")): return "naval"
    if any(k in vt for k in ("fighter", "assault", "bomber", "strike",
                             "aircraft", "attacker")): return "air"
    return "ground"

# tracker vehicles: name -> (branch, [alternative required-substring sets])
WANTED = {
 "M1A2 SEPv3": ("ground", [["sepv3"], ["m1a2c"], ["m1a2", "sep", "3"]]),
 "M1A2 (Trophy-HV)": ("ground", [["m1a2", "trophy"], ["abrams", "trophy"]]),
 "M60A1 Predator": ("ground", [["m60a1", "predator"], ["predator"]]),
 "Hummel": ("ground", [["hummel"]]),
 "Puma u14": ("ground", [["puma", "u14"], ["puma", "vjtf"]]),
 "T-90M (Arena-M)": ("ground", [["t90m", "arena"]]),
 "M1A1 (Australia)": ("ground", [["m1a1", "australia"], ["m1a1", "aim"]]),
 "M1A2 (Australia)": ("ground", [["m1a2", "australia"], ["m1a2", "kew"]]),
 "Leopard 2RI (Indonesia)": ("ground", [["2ri"]]),
 "PGZ88": ("ground", [["pgz88"], ["pgz", "88"]]),
 "Palmaria": ("ground", [["palmaria"]]),
 "Leopard 1A5BE (Belgium)": ("ground", [["1a5be"], ["leopard", "1a5", "be"]]),
 "NOMADS (Norway)": ("ground", [["nomads"]]),
 "Hunter AFV (Singapore)": ("ground", [["hunter", "afv"], ["hunter"]]),
 "F-101C Voodoo": ("air", [["f101c"]]),
 "F-14D Super Tomcat": ("air", [["f14d"]]),
 "Fw 189 C": ("air", [["fw189"]]),
 "IA.58A Pucara (Argentina)": ("air", [["pucara"]]),
 "Yak-130": ("air", [["yak130"]]),
 "J-22M1A (Serbia)": ("air", [["j22m"], ["j22"]]),
 "MiG-29KR (9-41R)": ("air", [["mig29kr"], ["mig29k"]]),
 "Washington B.Mk.I": ("air", [["washington"]]),
 "Welkin F.Mk.I": ("air", [["welkin"]]),
 "L-39ZA/ART Albatros (Thailand)": ("air", [["l39za"], ["l39"]]),
 "JH-7A2": ("air", [["jh7a2"]]),
 "F-16V": ("air", [["f16v"], ["f16", "block70"]]),
 "M-346FA": ("air", [["m346"]]),
 "F-16AM (Netherlands)": ("air", [["f16am"]]),
 "AJS37 (Early)": ("air", [["ajs37"]]),
 "MiG-21 2000": ("air", [["mig21", "2000"]]),
 "Mi-24D": ("heli", [["mi24d"]]),
 "USS North Carolina": ("naval", [["northcarolina"]]),
 "USS Gridley": ("naval", [["gridley"]]),
 "Lorelei": ("naval", [["lorelei"]]),
 "Admiral Scheer": ("naval", [["scheer"]]),
 "Chervona Ukraina": ("naval", [["chervona"]]),
 "HMS Egret": ("naval", [["egret"]]),
 "MTB-523": ("naval", [["mtb", "523"]]),
 "JDS Ujishima (MSC-655)": ("naval", [["ujishima"]]),
 "MAS 429": ("naval", [["mas", "429"]]),
 "Jean Bart": ("naval", [["jeanbart"], ["jean", "bart"]]),
}

brs = {}
try:
    all_vehicles, page = [], 0
    while page < 30:
        batch = json.loads(get(API % page))
        if not isinstance(batch, list) or not batch:
            break
        all_vehicles.extend(batch)
        if len(batch) < 200:
            break
        page += 1
    print("fetched", len(all_vehicles), "vehicles from datamine API")
    for name, (branch, alts) in WANTED.items():
        best, bs = None, 0
        for v in all_vehicles:
            ident = norm(v.get("identifier"))
            if not ident or branch_of(v.get("vehicle_type")) != branch:
                continue
            for tokens in alts:
                if all(t in ident for t in tokens):
                    # prefer more specific matches, shorter identifiers on tie
                    score = sum(len(t) for t in tokens) + (100 - len(ident)) * 0.01
                    if score > bs:
                        bs, best = score, v
                    break
        if best:
            brs[name] = {"ab": best.get("arcade_br"),
                         "rb": best.get("realistic_br") or best.get("realistic_ground_br"),
                         "sb": best.get("simulator_br") or best.get("simulator_ground_br"),
                         "rank": best.get("era"), "ident": best.get("identifier")}
    print("matched BRs for", len(brs), "of", len(WANTED), "vehicles:")
    for k, v in sorted(brs.items()):
        print("  %-32s -> %-28s AB %-5s RB %-5s SB %-5s" % (k, v["ident"], v["ab"], v["rb"], v["sb"]))
except Exception as e:
    print("BR fetch failed (page will show fallback note):", e)

out = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "latest_changelog": latest, "news": news[:20], "brs": brs}
os.makedirs("data", exist_ok=True)
with open("data/live.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote data/live.json")
