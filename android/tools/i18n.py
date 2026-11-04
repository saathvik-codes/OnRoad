"""
Builds the app's translations: every English UI string in the Kotlin sources -> app/src/main/assets/i18n/<lang>.json.

Strings with $name / ${expr} become templates ("Live offers in {0}") that AppLanguage matches at runtime.
Machine-translated in batches; a translation that loses a {n} placeholder is dropped (English is shown instead).
Existing files are kept and only new strings are translated, so hand fixes in the JSON survive.

    python android/tools/i18n.py
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app" / "src" / "main"
ROOT = Path(__file__).resolve().parents[2]
EXTRA = ["Choose your language", "You can change it any time in Profile."]
SRC = APP / "java" / "com" / "onroad" / "app"
OUT = APP / "assets" / "i18n"
LANGS = ["hi", "te", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "es", "fr", "de", "ar"]
LIT = re.compile(r'(?<!["\\])"((?:[^"\\\n$]|\\.|\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_.]*|\$)*)"')
SKIP = re.compile(r"https?:|^[a-z0-9_./{}-]+$|^#|^[A-Z0-9_]+$|%[sd]|\.(png|webp|jpg|json)$|^\W*$")


def template(s: str) -> str | None:
    n = [0]

    def sub(_):
        n[0] += 1
        return "{%d}" % (n[0] - 1)
    t = re.sub(r"\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", sub, s)
    t = t.replace('\\"', '"').replace("\\n", "\n").replace("\\$", "$")
    if not re.search(r"[A-Za-z]{2}", re.sub(r"\{\d+\}", "", t)) or SKIP.search(t) or len(t) > 400:
        return None
    if not (" " in t.strip() or t[:1].isupper()):
        return None
    return t


def strings() -> list[str]:
    found = set()
    for f in SRC.rglob("*.kt"):
        if f.name == "AppLanguage.kt":
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            code = line.split("//", 1)[0] if '"' not in line.split("//", 1)[-1] else line
            if re.search(r"\b(navigate|composable|route|getString|putString|Log\.|Regex|split|startsWith|contains|@SerialName)\b", code):
                continue
            for m in LIT.finditer(code):
                t = template(m.group(1))
                if t:
                    found.add(t)
    # wording the server sends: price-breakdown lines and spec names / groups
    calc = ROOT / "backend" / "onroad" / "onroad_calc.py"
    for m in re.finditer(r'"([A-Z][^"{}\n]{2,80})"', calc.read_text(encoding="utf-8")):
        if template(m.group(1)):
            found.add(m.group(1))
    found.update(EXTRA)
    try:
        import sqlite3
        c = sqlite3.connect(ROOT / "data" / "onroad.db")
        for (lab,) in c.execute("SELECT label FROM specs GROUP BY label ORDER BY COUNT(*) DESC LIMIT 200"):
            if lab and template(lab):
                found.add(lab)
        for (g,) in c.execute("SELECT DISTINCT grp FROM specs"):
            if g and template(g):
                found.add(g)
    except Exception:
        pass
    return sorted(found)


def gtx(texts: list[str], lang: str) -> list[str] | None:
    q = "\n".join(t.replace("\n", " ") for t in texts)
    data = urllib.parse.urlencode({"q": q}).encode()
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={lang}&dt=t"
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = "".join(seg[0] for seg in json.load(r)[0] if seg[0])
            lines = out.split("\n")
            return lines if len(lines) == len(texts) else None
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None


def translate(texts: list[str], lang: str) -> dict[str, str]:
    done, i = {}, 0
    while i < len(texts):
        batch, size = [], 0
        while i + len(batch) < len(texts) and size < 3000 and len(batch) < 60:
            batch.append(texts[i + len(batch)]); size += len(batch[-1]) + 1
        got = gtx(batch, lang)
        pairs = zip(batch, got) if got else ((t, (gtx([t], lang) or [None])[0]) for t in batch)
        for en, tr in pairs:
            if tr and sorted(re.findall(r"\{\d+\}", en)) == sorted(re.findall(r"\{\d+\}", tr)):
                done[en] = tr.strip()
        i += len(batch)
        time.sleep(1)
    return done


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    texts = strings()
    print(len(texts), "strings")
    for lang in LANGS:
        f = OUT / f"{lang}.json"
        have = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        todo = [t for t in texts if t not in have]
        have.update(translate(todo, lang) if todo else {})
        have = {k: v for k, v in have.items() if k in texts}
        f.write_text(json.dumps(have, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
        print(lang, len(have), "/", len(texts), flush=True)
