#!/usr/bin/env python3
"""Build the BookLock catalog from tools/sources.json.

    python tools/prep.py build [--only ID] [--draft]
    python tools/prep.py segment ID [--force]   # propose ~10-minute segments, report them
    python tools/prep.py text ID                # dump chapter/segment text to tools/work/ID/
    python tools/prep.py review ID              # readable segment quizzes in tools/work/ID/review.md
    python tools/prep.py covers [ID ...]        # find cover candidates and open a page to choose them

--draft allows missing quizzes so text can be extracted before quizzes exist; quizzes
that are present are still checked. Drafts are never valid for publishing: catalog.json
is only written on a full build.
"""
import argparse
import base64
import csv
import hashlib
import http.server
import io
import json
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from pathlib import Path

import pymupdf
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
BOOKS = ROOT / "books"
CACHE = TOOLS / ".cache"
WORK = TOOLS / "work"
SEGMENTS = TOOLS / "segments"
FORMAT_VERSION = 1
MAX_IMAGE_WIDTH = 1024
JPEG_QUALITY = 80

ALLOWED_LICENCES = {
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC0 1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "Public domain": None,
}

GENRES = ["Adventure", "Fantasy", "Animals", "Family & friends", "Mystery", "How things work", "Funny"]

# A book counts as a "picture book" once at least half its pages carry a picture, or
# "illustrated" for anything less than that but more than none. The cover doesn't count.
PICTURE_BOOK_RATIO = 0.5


SEGMENT_MINUTES = 10
COMPREHENSION_PER_SEGMENT = 3


def words_per_minute(age):
    # The app's reading-speed table (BL-24), applied to the book's youngest reader.
    # Under 6 isn't in that table; 50 is a guess for early readers.
    if age >= 12:
        return 180
    if age >= 10:
        return 150
    if age >= 8:
        return 110
    if age >= 6:
        return 70
    return 50


def pictures_label(chapters):
    pages = [p for c in chapters for p in c["pages"]]
    if not pages:
        return None
    ratio = sum(1 for p in pages if p["image"]) / len(pages)
    if ratio >= PICTURE_BOOK_RATIO:
        return "picture-book"
    if ratio > 0:
        return "illustrated"
    return None

# StoryWeaver PDFs encode these ligatures as accented letters.
SW_LIGATURES = {"ì": "fi", "ë": "ff", "í": "fl", "î": "ffi", "ï": "ffl"}

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


class PrepError(Exception):
    pass


def roman_to_int(s):
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = ROMAN[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / hashlib.sha1(url.encode()).hexdigest()
    if not path.exists():
        # Wikimedia asks for a User-Agent that says who's calling.
        req = urllib.request.Request(url, headers={
            "User-Agent": "BookLock catalog prep (https://github.com/jessesomething/book-lock-catalog)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
    return path.read_bytes()


def save_image(data, out_path, crop=None):
    img = Image.open(io.BytesIO(data))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    if crop:
        w, h = img.size
        img = img.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    if img.width > MAX_IMAGE_WIDTH:
        img = img.resize((MAX_IMAGE_WIDTH, round(img.height * MAX_IMAGE_WIDTH / img.width)), Image.LANCZOS)
    img.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True)


def clean_text(text, replacements):
    text = text.replace(" ", " ")
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def split_long(paragraph, page_words):
    if len(paragraph.split()) <= page_words * 1.3:
        return [paragraph]
    sentences = re.split(r"(?<=[.!?”’\"])\s+(?=[A-Z“‘\"])", paragraph)
    parts, current = [], []
    for s in sentences:
        if current and len(" ".join(current + [s]).split()) > page_words:
            parts.append(" ".join(current))
            current = []
        current.append(s)
    parts.append(" ".join(current))
    return parts


def to_parts(paragraphs, page_words):
    return [part for para in paragraphs for part in split_long(para, page_words)]


def paginate(parts, page_words):
    pages, current, count = [], [], 0
    for p in parts:
        if current and count + len(p.split()) > page_words:
            pages.append("\n\n".join(current))
            current, count = [], 0
        current.append(p)
        count += len(p.split())
    if current:
        pages.append("\n\n".join(current))
    return pages


# --- StoryWeaver (PDF inside the downloaded zip) ---------------------------------

def build_storyweaver(src, out_dir):
    zpath = ROOT / src["file"]
    if not zpath.exists():
        raise PrepError(f"{zpath} not found - copy the StoryWeaver download into sources/")
    with zipfile.ZipFile(zpath) as z:
        pdf_name = next(n for n in z.namelist() if n.endswith(".pdf"))
        attr_name = next(n for n in z.namelist() if n.startswith("StoryWeaverAttribution"))
        pdf = pymupdf.open(stream=z.read(pdf_name), filetype="pdf")
        attribution = z.read(attr_name).decode("utf-8")

    m = re.search(r"Attribution Text:\s*(.+?)\n", attribution)
    if not m:
        raise PrepError("no attribution text in StoryWeaver zip")
    credit = m.group(1).strip()
    lic = re.search(r"under a (CC[^ ]* [^ ]*|CC BY[- A-Z]*\d\.\d) license", credit)
    licence = lic.group(1).replace("-", " ").strip() if lic else None
    if licence == "CC BY SA 4.0":
        licence = "CC BY-SA 4.0"

    year_match = re.search(r"©[^)]*?(\d{4})", credit)
    if not year_match:
        raise PrepError(f"couldn't find a © year in the StoryWeaver attribution: {credit!r}")
    year = int(year_match.group(1))

    replacements = dict(SW_LIGATURES)
    replacements.update(src.get("replace", {}))

    first = " ".join(pdf[0].get_text().split())
    author = re.search(r"Author:\s*(.+?)\s*Illustrator:", first)
    illustrator = re.search(r"Illustrator:\s*(.+)$", first)

    cover_xref = max(pdf[0].get_images(full=True), key=lambda im: im[2] * im[3])[0]
    save_image(pdf.extract_image(cover_xref)["image"], out_dir / "cover.jpg")

    pages, image_credits = [], []
    for i in range(1, pdf.page_count):
        page = pdf[i]
        raw = page.get_text()
        if "made possible by Pratham Books" in raw:
            credits_text = clean_text(raw, replacements)
            ic = re.search(r"Images Attributions:\s*(.+)", credits_text, re.S)
            if ic:
                image_credits.append(" ".join(ic.group(1).split()))
            continue
        if raw.strip().startswith("This is a Level"):
            continue
        text = re.sub(r"^\s*\d+/\d+\s*$", "", raw, flags=re.M)
        text = re.sub(r"\s*\n\s*", " ", clean_text(text, replacements)).strip()
        images = page.get_images(full=True)
        name = None
        if images:
            xref = max(images, key=lambda im: im[2] * im[3])[0]
            name = f"p{len(pages) + 1:02d}.jpg"
            save_image(pdf.extract_image(xref)["image"], out_dir / name)
        pages.append({"text": text, "image": name})

    return {
        "title": src.get("title") or pdf.metadata.get("title") or first.split(" Author:")[0],
        "authors": src.get("authors") or [author.group(1).strip()],
        "illustrators": src.get("illustrators") or [illustrator.group(1).strip()],
        "licence": licence,
        "credit": credit,
        "imageCredits": " ".join(image_credits) or None,
        "changes": "Adapted for BookLock: pages re-laid out for phone screens, and comprehension quizzes added.",
        "cover": "cover.jpg",
        "chapters": [{"title": None, "pages": pages}],
        "year": year,
    }


# --- Gutenberg-sourced public-domain texts ---------------------------------------

def gutenberg_soup(ebook):
    base = f"https://www.gutenberg.org/cache/epub/{ebook}/"
    html = fetch(f"{base}pg{ebook}-images.html").decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    for x in soup.select("#pg-header, #pg-footer, section.pg-boilerplate"):
        x.decompose()
    return soup, base


def build_gutenberg(src, out_dir):
    soup, base = gutenberg_soup(src["ebook"])
    replacements = src.get("replace", {})
    skip_texts = set(src.get("skipParagraphs", []))
    skip_images = set(src.get("skipImages", []))
    page_words = src["pageWords"]

    cover = None
    if src.get("cover"):
        # A path inside this edition, or a full URL chosen on the `prep.py covers` page.
        url = src["cover"] if src["cover"].startswith("http") else base + src["cover"]
        save_image(fetch(url), out_dir / "cover.jpg", src.get("coverCrop"))
        cover = "cover.jpg"

    elements = soup.body.find_all(["h2", "p", "img"])
    start = src.get("startAt")
    if start:
        idx = next((i for i, el in enumerate(elements)
                    if el.name == "p" and " ".join(el.get_text().split()).startswith(start)), None)
        if idx is None:
            raise PrepError(f"startAt text not found: {start!r}")
        elements = elements[idx:]

    if src["kind"] == "picture":
        chapters = [{"title": None, "pages": picture_pages(elements, base, out_dir, page_words,
                                                           replacements, skip_texts, skip_images)}]
    else:
        chapters = chapter_pages(elements, page_words, replacements, skip_texts)

    return {
        "title": src["title"],
        "authors": src["authors"],
        "illustrators": src.get("illustrators", []),
        "licence": "Public domain",
        "credit": src["credit"],
        "imageCredits": None,
        "changes": "Adapted for BookLock: text split into pages for phone screens, and comprehension quizzes added.",
        "cover": cover,
        "chapters": chapters,
        "year": src["year"],
    }


def picture_pages(elements, base, out_dir, page_words, replacements, skip_texts, skip_images):
    pages, current_img, paras, n_img = [], None, [], 0

    def flush():
        nonlocal paras, current_img
        if not paras and current_img is None:
            return
        chunks = paginate(to_parts(paras, page_words), page_words) or [""]
        for j, chunk in enumerate(chunks):
            pages.append({"text": chunk, "image": current_img if j == 0 else None})
        paras, current_img = [], None

    for el in elements:
        if el.name == "img":
            src = el.get("src")
            if src in skip_images:
                continue
            flush()
            n_img += 1
            current_img = f"p{n_img:02d}.jpg"
            save_image(fetch(base + src), out_dir / current_img)
        elif el.name == "p":
            t = clean_text(" ".join(el.get_text().split()), replacements)
            if t and t not in skip_texts:
                paras.append(t)
    flush()
    return pages


CHAPTER_RE = re.compile(r"^chapter\s+([IVXLC]+)\b\.?\s*(.*)$", re.I)


def chapter_pages(elements, page_words, replacements, skip_texts):
    chapters, current = [], None
    for el in elements:
        if el.name == "h2":
            m = CHAPTER_RE.match(" ".join(el.get_text().split()))
            if m:
                name = m.group(2).strip().rstrip(".")
                current = {"title": f"Chapter {roman_to_int(m.group(1))}" + (f": {name}" if name else ""),
                           "paras": []}
                chapters.append(current)
            elif current is not None and chapters:
                current = None  # a non-chapter h2 after the chapters (e.g. an appendix) ends the text
        elif el.name == "p" and current is not None:
            t = clean_text(" ".join(el.get_text().split()), replacements)
            if t and t not in skip_texts:
                current["paras"].append(t)
    if not chapters:
        raise PrepError("no chapter headings found")
    # Paginated later, once segment starts are known, so each segment starts on a fresh page.
    return [{"title": c["title"], "parts": to_parts(c["paras"], page_words)} for c in chapters]


# --- Segments --------------------------------------------------------------------
#
# A segment is ~10 minutes of reading; the app strings segments together into a sitting.
# tools/segments/<id>.json lists where each segment starts: {"chapter": N} for the top of a
# chapter, plus "startsWith" (a paragraph's opening words; a page's, in picture books) for a
# start inside one. Each segment runs until the next one starts.

QUOTE_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "—": "-", "–": "-", " ": " "})
EVIDENCE_EDGE = " \"'.,;:!?-"


def norm(text):
    return re.sub(r"\s+", " ", text.translate(QUOTE_MAP)).strip().lower()


def chapter_units(chapters):
    """Per chapter, the pieces a segment may start at."""
    return [c["parts"] if "parts" in c else [p["text"] for p in c["pages"]] for c in chapters]


def load_segment_starts(book_id, units):
    path = SEGMENTS / f"{book_id}.json"
    if not path.exists():
        return None
    starts = []
    for n, entry in enumerate(json.loads(path.read_text())["segments"], 1):
        ci = entry["chapter"] - 1
        if not 0 <= ci < len(units):
            raise PrepError(f"{path.name}: segment {n} starts in chapter {ci + 1}, which doesn't exist")
        ui = 0
        if "startsWith" in entry:
            key = norm(entry["startsWith"])
            hits = [i for i, u in enumerate(units[ci]) if norm(u).startswith(key)]
            if len(hits) != 1:
                raise PrepError(f"{path.name}: segment {n}: startsWith matches {len(hits)} places "
                                f"in chapter {ci + 1}: {entry['startsWith']!r}")
            ui = hits[0]
        starts.append((ci, ui))
    if not starts or starts[0] != (0, 0):
        raise PrepError(f"{path.name}: the first segment must start at the top of chapter 1")
    if any(b <= a for a, b in zip(starts, starts[1:])):
        raise PrepError(f"{path.name}: segments must be in reading order, with no repeats")
    return starts


def lay_out(chapters, starts, page_words):
    """Paginate chapter books with a page break at every segment start, and turn segment
    starts from (chapter, unit) into (chapter, page)."""
    page_starts = []
    for ci, c in enumerate(chapters):
        cuts = [ui for sci, ui in starts if sci == ci]
        if "parts" not in c:
            page_starts += [(ci, ui) for ui in cuts]
            continue
        bounds = sorted({0, *cuts, len(c["parts"])})
        pages = []
        for a, b in zip(bounds, bounds[1:]):
            if a in cuts:
                page_starts.append((ci, len(pages)))
            pages += paginate(c["parts"][a:b], page_words)
        c["pages"] = [{"text": t, "image": None} for t in pages]
        del c["parts"]
    return page_starts


def page_positions(chapters):
    return [(ci, pi) for ci, c in enumerate(chapters) for pi in range(len(c["pages"]))]


def pages_in(chapters, seg):
    flat = page_positions(chapters)
    a = flat.index((seg["startChapter"], seg["startPage"]))
    b = flat.index((seg["endChapter"], seg["endPage"]))
    return flat[a:b + 1]


def segment_text(chapters, pages):
    return norm(" ".join(chapters[ci]["pages"][pi]["text"] for ci, pi in pages))


def check_choice_question(q, where):
    if not (2 <= len(q["choices"]) <= 4) or not (0 <= q["correctIndex"] < len(q["choices"])):
        raise PrepError(f"{where}: bad question {q['prompt']!r}")


def evidence_fragments(evidence):
    quotes = [evidence] if isinstance(evidence, str) else (evidence or [])
    frags = [f.strip(EVIDENCE_EDGE) for q in quotes for f in re.split(r"\.\.\.|…", norm(q))]
    return [f for f in frags if f]


def check_evidence(q, allowed, later, where):
    frags = evidence_fragments(q.get("evidence"))
    if not frags or max(len(f.split()) for f in frags) < 4:
        raise PrepError(f"{where}: {q['prompt']!r} needs an evidence quote of at least 4 words")
    for f in frags:
        if f not in allowed:
            hint = " (it comes later in the book, so the question would spoil it)" if f in later else ""
            raise PrepError(f"{where}: evidence for {q['prompt']!r} isn't in the text{hint}: {f!r}")


def shipped_question(q):
    # "evidence" is for review and checking only; it doesn't ship in book.json.
    return {k: q[k] for k in ("prompt", "choices", "correctIndex")}


def load_segment_quizzes(book_id, texts, draft):
    """texts: each segment's normalised text. Comprehension evidence must come from the
    segment itself; theme evidence from it or any earlier segment, never a later one.

    Theme and written questions come as a pair on roughly every other segment: never two
    segments in a row without them (so any sitting of two or more segments gets one), and
    always on the last segment."""
    path = TOOLS / "quizzes" / f"{book_id}.json"
    quizzes = json.loads(path.read_text()).get("segments", []) if path.exists() else []
    if len(quizzes) > len(texts):
        raise PrepError(f"{path.name} has {len(quizzes)} segment quizzes, book has {len(texts)} segments")
    if len(quizzes) < len(texts) and not draft:
        raise PrepError(f"{path.name}: only {len(quizzes)} of {len(texts)} segments have quizzes")
    shipped = []
    for si, quiz in enumerate(quizzes):
        where = f"{path.name}: segment {si + 1}"
        questions, theme, written = quiz.get("questions", []), quiz.get("theme"), (quiz.get("written") or "").strip()
        if len(questions) != COMPREHENSION_PER_SEGMENT:
            raise PrepError(f"{where} needs {COMPREHENSION_PER_SEGMENT} comprehension questions")
        if bool(theme) != bool(written):
            raise PrepError(f"{where}: theme and written questions go together - give it both or neither")
        later = " ".join(texts[si + 1:])
        for q in questions:
            check_choice_question(q, where)
            check_evidence(q, texts[si], later, where)
        if theme:
            check_choice_question(theme, where)
            check_evidence(theme, " ".join(texts[:si + 1]), later, where)
        shipped.append({"questions": [shipped_question(q) for q in questions],
                        "theme": shipped_question(theme) if theme else None,
                        "written": written or None})
    has_theme = [s["theme"] is not None for s in shipped]
    for si in range(len(has_theme) - 1):
        if not has_theme[si] and not has_theme[si + 1]:
            raise PrepError(f"{path.name}: segments {si + 1} and {si + 2} both lack theme and written "
                            f"questions - one of every two in a row needs them")
    if len(shipped) == len(texts) and texts and not has_theme[-1]:
        raise PrepError(f"{path.name}: the last segment needs theme and written questions")
    return shipped + [None] * (len(texts) - len(quizzes))


# A segment shouldn't open mid-conversation; it reads best where the story shifts time or place.
DIALOGUE_OPENING = re.compile(r"^[“\"‘']")
SCENE_SHIFT = re.compile(
    r"^(The next (morning|day|night|evening)|Next (morning|day)|The following|"
    r"That (night|evening|afternoon|morning)|In the (morning|afternoon|evening)|Early (the|in|one|next)|"
    r"One (day|morning|evening|night)|Some (time|days|hours|weeks) (later|after)|By and by|Meanwhile)\b",
    re.I)
SCENE_SHIFT_PULL = 0.3  # a time shift beats a closer plain paragraph within this share of a segment
MID_TALK_PUSH = 0.3     # and a cut between two lines of one conversation is pushed away by the same


def pick_cut(chapter, candidates, before, goal, target):
    def cost(i):
        c = abs(before[i] - goal)
        if SCENE_SHIFT.match(chapter[i]):
            c -= SCENE_SHIFT_PULL * target
        if DIALOGUE_OPENING.match(chapter[i - 1]) and i + 1 < len(chapter) and DIALOGUE_OPENING.match(chapter[i + 1]):
            c += MID_TALK_PUSH * target
        return c

    allowed = [i for i in candidates
               if not DIALOGUE_OPENING.match(chapter[i]) and not chapter[i - 1].rstrip().endswith(":")]
    return min(allowed or candidates, key=cost)


def propose_starts(units, target):
    """Pack short chapters together and split long ones evenly, aiming for `target` words.
    Cuts inside a chapter avoid dialogue and lean toward time or place shifts."""
    starts, open_words = [], 0
    for ci, ch in enumerate(units):
        ws = [len(u.split()) for u in ch]
        total = sum(ws)
        n = min(len(ws), max(1, int(total / target + 0.5)))
        if n == 1:
            if starts and (open_words + total <= 1.3 * target or open_words < 0.5 * target):
                open_words += total
                continue
            starts.append((ci, 0))
            open_words = total
            continue
        starts.append((ci, 0))
        before = [sum(ws[:i]) for i in range(len(ws))]
        last = 0
        for k in range(1, n):
            goal = total * k / n
            last = pick_cut(ch, range(last + 1, len(ws) - (n - 1 - k)), before, goal, target)
            starts.append((ci, last))
        open_words = total - before[last]
    if len(starts) > 1 and open_words < 0.5 * target:
        starts.pop()
    return starts


def opening_words(chapter, ui):
    words = chapter[ui].split()
    for k in range(min(6, len(words)), len(words) + 1):
        key = norm(" ".join(words[:k]))
        if sum(norm(u).startswith(key) for u in chapter) == 1:
            return " ".join(words[:k])
    raise PrepError(f"paragraph is repeated word for word in its chapter: {chapter[ui][:60]!r}")


def write_segments(path, units, starts):
    entries = [{"chapter": ci + 1} if ui == 0 else {"chapter": ci + 1, "startsWith": opening_words(units[ci], ui)}
               for ci, ui in starts]
    lines = ",\n".join("  " + json.dumps(e, ensure_ascii=False) for e in entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{\n "segments": [\n' + lines + "\n ]\n}\n")


# --- Assembly --------------------------------------------------------------------

def load_quizzes(book_id, chapter_count, draft):
    path = TOOLS / "quizzes" / f"{book_id}.json"
    if not path.exists():
        if draft:
            return [[] for _ in range(chapter_count)]
        raise PrepError(f"missing quizzes: {path.relative_to(ROOT)}")
    quizzes = json.loads(path.read_text())["chapters"]
    if len(quizzes) != chapter_count and not draft:
        raise PrepError(f"{path.name} has {len(quizzes)} chapter quizzes, book has {chapter_count} chapters")
    for ci, quiz in enumerate(quizzes):
        if not quiz and not draft:
            raise PrepError(f"{path.name}: chapter {ci + 1} has no questions")
        for q in quiz:
            if not (2 <= len(q["choices"]) <= 4) or not (0 <= q["correctIndex"] < len(q["choices"])):
                raise PrepError(f"{path.name}: bad question in chapter {ci + 1}: {q['prompt']!r}")
    quizzes += [[] for _ in range(chapter_count - len(quizzes))]
    return [[shipped_question(q) for q in quiz] for quiz in quizzes[:chapter_count]]


def build_book(src, draft):
    # Built beside the real folder and swapped in only on success, so a failed build
    # never leaves a published book half-deleted.
    final = BOOKS / src["id"]
    staging = BOOKS / f".{src['id']}.building"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    try:
        book_json = assemble_book(src, draft, staging)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    shutil.rmtree(final, ignore_errors=True)
    staging.rename(final)
    return book_json


def assemble_book(src, draft, out_dir):
    builder = {"storyweaver": build_storyweaver, "gutenberg": build_gutenberg}[src["source"]]
    book = builder(src, out_dir)

    if book["licence"] not in ALLOWED_LICENCES:
        raise PrepError(f"{src['id']}: licence {book['licence']!r} is not allowed")

    genre = src.get("genre")
    if genre not in GENRES:
        raise PrepError(f"{src['id']}: genre {genre!r} must be one of {GENRES}")

    starts = load_segment_starts(src["id"], chapter_units(book["chapters"]))
    page_starts = lay_out(book["chapters"], starts or [], src.get("pageWords"))

    quizzes = load_quizzes(src["id"], len(book["chapters"]), draft)
    for chapter, quiz in zip(book["chapters"], quizzes):
        chapter["quiz"] = quiz

    segments = None
    if starts:
        flat = page_positions(book["chapters"])
        firsts = [flat.index(p) for p in page_starts]
        ranges = [flat[a:b] for a, b in zip(firsts, firsts[1:] + [len(flat)])]
        texts = [segment_text(book["chapters"], r) for r in ranges]
        segments = [{"startChapter": r[0][0], "startPage": r[0][1],
                     "endChapter": r[-1][0], "endPage": r[-1][1],
                     "wordCount": sum(len(book["chapters"][ci]["pages"][pi]["text"].split()) for ci, pi in r),
                     "quiz": quiz}
                    for r, quiz in zip(ranges, load_segment_quizzes(src["id"], texts, draft))]
    else:
        qpath = TOOLS / "quizzes" / f"{src['id']}.json"
        if qpath.exists() and json.loads(qpath.read_text()).get("segments"):
            raise PrepError(f"{qpath.name} has segment quizzes but tools/segments/{src['id']}.json is missing")

    words = sum(len(p["text"].split()) for c in book["chapters"] for p in c["pages"])
    book_json = {
        "formatVersion": FORMAT_VERSION,
        "id": src["id"],
        "title": book["title"],
        "authors": book["authors"],
        "illustrators": book["illustrators"],
        "minAge": src["minAge"],
        "maxAge": src["maxAge"],
        "cover": book["cover"],
        "licence": {"name": book["licence"], "url": ALLOWED_LICENCES[book["licence"]]},
        "year": book["year"],
        "genre": genre,
        "classic": src.get("classic", False),
        "pictures": pictures_label(book["chapters"]),
        "credit": book["credit"],
        "imageCredits": " ".join(c for c in (book["imageCredits"], src.get("coverCredit")) if c) or None,
        "changes": book["changes"],
        "wordCount": words,
        "chapters": book["chapters"],
    }
    if segments:
        book_json["segments"] = segments
    (out_dir / "book.json").write_text(json.dumps(book_json, ensure_ascii=False, indent=1))

    odd = sorted({ch for c in book["chapters"] for p in c["pages"] for ch in p["text"]
                  if ord(ch) > 127 and ch not in "‘’“”—–…é"})
    if odd:
        print(f"  note: {src['id']} contains unusual characters {''.join(odd)!r} - check the text")
    return book_json


def catalog_entry(book_json, starter):
    book_dir = BOOKS / book_json["id"]
    files = sorted(f.name for f in book_dir.iterdir() if f.is_file())
    h = hashlib.sha256()
    for name in files:
        h.update(name.encode())
        h.update((book_dir / name).read_bytes())
    return {
        "id": book_json["id"],
        "title": book_json["title"],
        "authors": book_json["authors"],
        "illustrators": book_json["illustrators"],
        "minAge": book_json["minAge"],
        "maxAge": book_json["maxAge"],
        "cover": f"books/{book_json['id']}/{book_json['cover']}" if book_json["cover"] else None,
        "licence": book_json["licence"],
        "credit": book_json["credit"],
        "chapterCount": len(book_json["chapters"]),
        "wordCount": book_json["wordCount"],
        "year": book_json["year"],
        "genre": book_json["genre"],
        "classic": book_json["classic"],
        "pictures": book_json["pictures"],
        "files": [f"books/{book_json['id']}/{n}" for n in files],
        "sizeBytes": sum((book_dir / n).stat().st_size for n in files),
        "version": h.hexdigest()[:12],
        "starter": starter,
    }


def cmd_build(args):
    sources = json.loads((TOOLS / "sources.json").read_text())
    if args.only:
        sources = [s for s in sources if s["id"] == args.only]
        if not sources:
            raise PrepError(f"no source with id {args.only!r}")
    for src in sources:
        print(f"building {src['id']}")
        build_book(src, args.draft)

    if args.draft:
        print("draft build: catalog.json not updated")
        return
    all_sources = json.loads((TOOLS / "sources.json").read_text())
    entries = []
    for src in all_sources:
        book_id = src["id"]
        path = BOOKS / book_id / "book.json"
        if not path.exists():
            raise PrepError(f"{book_id} has not been built")
        book_json = json.loads(path.read_text())
        load_quizzes(book_id, len(book_json["chapters"]), draft=False)
        if any(not c["quiz"] for c in book_json["chapters"]):
            raise PrepError(f"{book_id} was built as a draft - rebuild it without --draft")
        if (SEGMENTS / f"{book_id}.json").exists():
            segs = book_json.get("segments") or []
            texts = [segment_text(book_json["chapters"], pages_in(book_json["chapters"], s)) for s in segs]
            if not segs or load_segment_quizzes(book_id, texts, draft=False) != [s["quiz"] for s in segs]:
                raise PrepError(f"{book_id}'s segments or quizzes changed since it was built - rebuild it")
        entries.append(catalog_entry(book_json, src.get("starter", False)))
    (ROOT / "catalog.json").write_text(json.dumps(
        {"formatVersion": FORMAT_VERSION, "books": entries}, ensure_ascii=False, indent=1))
    print(f"catalog.json: {len(entries)} books")


def source(book_id):
    for src in json.loads((TOOLS / "sources.json").read_text()):
        if src["id"] == book_id:
            return src
    raise PrepError(f"no source with id {book_id!r}")


def built_book(book_id):
    path = BOOKS / book_id / "book.json"
    if not path.exists():
        raise PrepError(f"{book_id} has not been built - run: prep.py build --only {book_id} --draft")
    return json.loads(path.read_text())


def built_units(src, book_json):
    """chapter_units() recovered from a built book.json: chapter books' pages are paragraphs
    joined by blank lines."""
    if src.get("kind") == "chapters":
        return [[u for p in c["pages"] for u in p["text"].split("\n\n")] for c in book_json["chapters"]]
    return [[p["text"] for p in c["pages"]] for c in book_json["chapters"]]


def cmd_segment(args):
    src = source(args.id)
    units = built_units(src, built_book(args.id))
    wpm = words_per_minute(src["minAge"])
    path = SEGMENTS / f"{args.id}.json"
    if args.force or not path.exists():
        write_segments(path, units, propose_starts(units, wpm * SEGMENT_MINUTES))
        print(f"wrote {path.relative_to(ROOT)} - move starts inside chapters onto scene breaks, then rebuild\n")

    starts = load_segment_starts(args.id, units)
    flat = [(ci, ui) for ci, ch in enumerate(units) for ui in range(len(ch))]
    words = [len(units[ci][ui].split()) for ci, ui in flat]
    firsts = [flat.index(s) for s in starts]
    for n, (a, b) in enumerate(zip(firsts, firsts[1:] + [len(flat)]), 1):
        ci, ui = flat[a]
        where = f"ch {ci + 1}" + (f"  {' '.join(units[ci][ui].split()[:6])}..." if ui else "")
        w = sum(words[a:b])
        print(f"{n:3}  {where:<52} {w:6} words {w / wpm:5.1f} min")
    print(f"\n{len(starts)} segments; aiming for {wpm * SEGMENT_MINUTES} words "
          f"({SEGMENT_MINUTES} min at {wpm} words/min for age {src['minAge']})")


def cmd_text(args):
    book = built_book(args.id)
    out = WORK / args.id
    out.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(book["chapters"], 1):
        body = "\n\n".join(p["text"] for p in c["pages"])
        (out / f"ch{i:02d}.txt").write_text(f"{c['title'] or book['title']}\n\n{body}\n")
    print(f"wrote {len(book['chapters'])} chapter files to {out.relative_to(ROOT)}")

    for old in out.glob("seg*.txt"):
        old.unlink()
    segments = book.get("segments") or []
    wpm = words_per_minute(book["minAge"])
    for si, seg in enumerate(segments, 1):
        chunks, last_ci = [], None
        for ci, pi in pages_in(book["chapters"], seg):
            if ci != last_ci:
                title = book["chapters"][ci]["title"] or book["title"]
                chunks.append(f"## {title}" + (" (continued)" if pi else ""))
                last_ci = ci
            chunks.append(book["chapters"][ci]["pages"][pi]["text"])
        header = (f"Segment {si} of {len(segments)} - {seg['wordCount']} words, "
                  f"about {round(seg['wordCount'] / wpm)} min")
        (out / f"seg{si:03d}.txt").write_text(header + "\n\n" + "\n\n".join(chunks) + "\n")
    if segments:
        print(f"wrote {len(segments)} segment files to {out.relative_to(ROOT)}")


def review_question(q, label):
    lines = [f"**{label}** {q['prompt']}", ""]
    lines += [f"- **{c}** ✓" if i == q["correctIndex"] else f"- {c}" for i, c in enumerate(q["choices"])]
    quotes = [q["evidence"]] if isinstance(q["evidence"], str) else q["evidence"]
    return lines + [""] + [line for e in quotes for line in (f"> {e}", "")]


def cmd_review(args):
    book = built_book(args.id)
    segments = book.get("segments") or []
    quizzes = json.loads((TOOLS / "quizzes" / f"{args.id}.json").read_text()).get("segments", [])
    chapters = book["chapters"]
    lines = [f"# {book['title']}: segment quizzes", "",
             f"{len(quizzes)} of {len(segments)} segments written. The build has checked every "
             "comprehension answer against the text, so those only need a skim (right answer in bold). "
             "**Read the theme questions** — those are the judgment calls.", ""]
    for si, (seg, quiz) in enumerate(zip(segments, quizzes), 1):
        pages = pages_in(chapters, seg)
        (ci, pi), (lci, lpi) = pages[0], pages[-1]
        title = chapters[ci]["title"] or book["title"]
        start = " ".join(chapters[ci]["pages"][pi]["text"].split()[:10])
        end = " ".join(chapters[lci]["pages"][lpi]["text"].split()[-10:])
        lines += [f"## Segment {si}: {title}{' (continued)' if pi else ''}", "",
                  f"*{seg['wordCount']} words. Starts \"{start} …\" and ends \"… {end}\"*", ""]
        for n, q in enumerate(quiz["questions"], 1):
            choices = " · ".join(f"**{c}**" if i == q["correctIndex"] else c for i, c in enumerate(q["choices"]))
            lines += [f"{n}. {q['prompt']} — {choices}"]
        lines += [""]
        if quiz.get("theme"):
            lines += review_question(quiz["theme"], "Theme:")
            lines += [f"**Written (for the parent):** {quiz['written']}", ""]
    out = WORK / args.id / "review.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"wrote {out.relative_to(ROOT)}")

# --- Cover candidates ------------------------------------------------------------

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PG_CATALOG = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
COVER_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/tiff", "image/webp"}
MIN_COVER_WIDTH = 300
COMMONS_PER_BOOK = 12
IMAGES_PER_EDITION = 3


def main_title(title):
    """"The Tale of Peter Rabbit; or, ..." -> "tale of peter rabbit", for matching editions."""
    words = re.sub(r"[^a-z0-9 ]+", " ", re.split(r"[:;\n]|, or\b", title.lower())[0]).split()
    return " ".join(words[1:] if words and words[0] in ("the", "a", "an") else words)


def commons_licence(meta):
    """The file's licence if the catalog's rules allow it (public domain, CC0, CC BY, CC BY-SA), else None."""
    value = lambda key: meta.get(key, {}).get("value", "")
    code = value("License").lower()
    if code in ("pd", "cc0") or value("Copyrighted") == "False":
        return value("LicenseShortName") or "Public domain"
    if re.fullmatch(r"cc-by(-sa)?-[\d.]+", code):
        return value("LicenseShortName")
    return None


def commons_candidates(src):
    title = src["title"]
    found, rejected = {}, 0
    for query in (f'"{title}" cover', f'"{title}" first edition'):
        params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": query,
                  "gsrnamespace": 6, "gsrlimit": 20, "prop": "imageinfo",
                  "iiprop": "url|size|mime|extmetadata", "iiurlwidth": MAX_IMAGE_WIDTH,
                  "iiextmetadatafilter": "License|LicenseShortName|Copyrighted|Artist|DateTimeOriginal"}
        pages = json.loads(fetch(f"{COMMONS_API}?{urllib.parse.urlencode(params)}"))
        for page in sorted(pages.get("query", {}).get("pages", {}).values(), key=lambda p: p["index"]):
            info = page["imageinfo"][0]
            # Covers are portrait; this also drops most photos of places and page spreads.
            if (page["title"] in found or info["mime"] not in COVER_IMAGE_TYPES
                    or info["width"] < MIN_COVER_WIDTH or info["width"] > info["height"]):
                continue
            meta = info.get("extmetadata", {})
            licence = commons_licence(meta)
            if not licence:
                rejected += 1
                continue
            artist = " ".join(BeautifulSoup(meta.get("Artist", {}).get("value", ""), "html.parser")
                              .get_text().split()).rstrip(",; ")
            date = " ".join(BeautifulSoup(meta.get("DateTimeOriginal", {}).get("value", ""), "html.parser").get_text().split())
            name = page["title"].removeprefix("File:")
            credit = f"Cover: {artist or name}{', ' + date if date else ''}, via Wikimedia Commons"
            credit += "." if licence.lower().startswith(("public domain", "pd")) else \
                f" ({info['descriptionurl']}), {licence}."
            found[page["title"]] = {
                "url": (info.get("thumburl") or info["url"]).split("?utm_")[0],
                "width": info["width"], "height": info["height"],
                "where": f"Wikimedia Commons: {name}", "link": info["descriptionurl"],
                "licence": licence, "by": artist, "date": date, "credit": credit}
    if rejected:
        print(f"  {rejected} Commons file(s) dropped for their licence")
    return list(found.values())[:COMMONS_PER_BOOK]


def illustrator_names(authors):
    """"Claus, M. A. (May Austin), 1882-1976 [Illustrator]" -> ["M. A. Claus"]."""
    names = []
    for part in authors.split(";"):
        if "[Illustrator]" not in part:
            continue
        name = re.sub(r"\s*\(.*?\)|,\s*[\d?]*-[\d?]*\s*$", "", part.split("[")[0].strip())
        last, _, first = name.partition(", ")
        names.append(f"{first} {last}".strip())
    return names


def edition_candidates(src):
    """Cover-like pictures (named cover or frontispiece, or the first picture) in other English
    editions of the same title."""
    title, surname = main_title(src["title"]), src["authors"][0].split()[-1]
    out = []
    for row in csv.DictReader(io.StringIO(fetch(PG_CATALOG).decode("utf-8"))):
        if (row["Type"] != "Text" or row["Language"] != "en" or row["Text#"] == str(src["ebook"])
                or main_title(row["Title"]) != title or surname not in row["Authors"]):
            continue
        try:
            soup, base = gutenberg_soup(row["Text#"])
        except urllib.error.HTTPError:
            continue
        imgs = list({im["src"]: im for im in soup.find_all("img") if im.get("src")}.values())
        coverish = [im for im in imgs if re.search(r"cover|front", " ".join(
            [im["src"], im.get("alt", ""), im.get("id", "")] + im.get("class", [])), re.I)]
        picks = (coverish if imgs[:1] and imgs[0] in coverish else imgs[:1] + coverish)[:IMAGES_PER_EDITION]
        illustrators = illustrator_names(row["Authors"])
        by = " and ".join(illustrators)
        for im in picks:
            width, height = Image.open(io.BytesIO(fetch(base + im["src"]))).size
            if width < MIN_COVER_WIDTH:
                continue
            out.append({
                "url": base + im["src"], "width": width, "height": height,
                "where": f"Gutenberg edition #{row['Text#']}: {im['src'].split('/')[-1]}",
                "link": f"https://www.gutenberg.org/ebooks/{row['Text#']}",
                "licence": "Public domain", "by": row["Authors"].replace("\n", " "), "date": "",
                # No Gutenberg name in credits - it's trademarked (see README, Licence rules).
                "credit": f"Cover: from the edition illustrated by {by}. Public domain." if by
                          else "Cover: from another public-domain edition."})
    return out


def cover_fields(src):
    return {k: src[k] for k in ("cover", "coverCrop", "coverCredit") if k in src}


def cover_snapshot(book_id):
    path = BOOKS / book_id / "cover.jpg"
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode() if path.exists() else None


def set_cover(book_id, fields):
    """Sets this book's cover keys in sources.json, touching only those lines so the file keeps its
    hand formatting: a key already there changes in place, a new one goes at the end, a dropped one
    goes. Putting back a book's original fields restores the file exactly."""
    path = TOOLS / "sources.json"
    lines = path.read_text().split("\n")
    start = next(i for i, line in enumerate(lines) if f'"id": "{book_id}"' in line)
    end = next(i for i in range(start, len(lines)) if lines[i].rstrip(",") == " }")
    entry = lambda k, v: f'  "{k}": {json.dumps(v, ensure_ascii=False)}'
    todo, body = dict(fields), []
    for line in lines[start:end]:
        key = re.match(r'\s*"(cover(?:Crop|Credit)?)":', line)
        if not key:
            body.append(line)
        elif key.group(1) in todo:
            body.append(entry(key.group(1), todo.pop(key.group(1))))
    body += [entry(k, v) for k, v in todo.items()]
    body = [line.rstrip(",") + "," for line in body[:-1]] + [body[-1].rstrip(",")]
    text = "\n".join(lines[:start] + body + lines[end:])
    json.loads(text)
    path.write_text(text)


def picker_state(covers):
    books = []
    for book_id, entry in covers.items():
        src = source(book_id)
        fields = cover_fields(src)
        path = BOOKS / book_id / "cover.jpg"
        books.append({
            "id": book_id, "title": src["title"],
            "current": f"/current/{book_id}.jpg?v={path.stat().st_mtime_ns}" if path.exists() else None,
            "credit": fields.get("coverCredit"),
            "crop": fields.get("coverCrop"),
            "original": entry["original"]["image"],
            "originalInUse": fields == entry["original"]["fields"],
            "inUse": next((i for i, c in enumerate(entry["candidates"]) if c["url"] == fields.get("cover")), None),
            "candidates": entry["candidates"]})
    return books


def apply_pick(covers, pick):
    book_id = pick["id"]
    entry = covers[book_id]
    if pick.get("original"):
        fields = entry["original"]["fields"]
    else:
        cand = entry["candidates"][int(pick["n"])]
        fields = {"cover": cand["url"], "coverCredit": " ".join(str(pick.get("credit") or cand["credit"]).split())}
        if pick.get("crop"):
            crop = [round(float(x), 3) for x in pick["crop"]]
            if len(crop) != 4 or not (0 <= crop[0] < crop[2] <= 1 and 0 <= crop[1] < crop[3] <= 1):
                raise PrepError(f"bad crop {crop}")
            fields["coverCrop"] = crop
    sources_path = TOOLS / "sources.json"
    before = sources_path.read_text()
    set_cover(book_id, fields)
    try:
        cmd_build(argparse.Namespace(only=book_id, draft=False))
    except BaseException:
        sources_path.write_text(before)  # the build swaps books in only on success, so this undoes it all
        raise


def serve_picker(covers, port):
    origin = f"http://127.0.0.1:{port}"

    class Handler(http.server.BaseHTTPRequestHandler):
        def reply(self, code, body, kind):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def reply_json(self, code, data):
            self.reply(code, json.dumps(data, ensure_ascii=False).encode(), "application/json")

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            current = re.fullmatch(r"/current/([a-z0-9-]+)\.jpg", path)
            if path == "/":
                self.reply(200, (TOOLS / "cover_picker.html").read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/books":
                self.reply_json(200, picker_state(covers))
            elif current and current.group(1) in covers and (BOOKS / current.group(1) / "cover.jpg").exists():
                self.reply(200, (BOOKS / current.group(1) / "cover.jpg").read_bytes(), "image/jpeg")
            else:
                self.reply(404, b"not found", "text/plain")

        def do_POST(self):
            # JSON only, from this page only: another site open in the browser can't make the
            # browser send this without being refused by the missing CORS headers.
            if (self.path != "/api/pick" or self.headers.get("Content-Type") != "application/json"
                    or self.headers.get("Origin") not in (None, origin)):
                return self.reply(403, b"refused", "text/plain")
            try:
                apply_pick(covers, json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            except Exception as e:
                return self.reply_json(400, {"error": str(e) or type(e).__name__})
            self.reply_json(200, picker_state(covers))

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"cover picker at {origin}/ - Ctrl-C to stop")
    webbrowser.open(origin + "/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()


def cmd_covers(args):
    path = WORK / "covers.json"
    covers = json.loads(path.read_text()) if path.exists() else {}
    for src in ([source(i) for i in args.ids] if args.ids else json.loads((TOOLS / "sources.json").read_text())):
        if src["source"] != "gutenberg":
            print(f"{src['id']}: skipped - StoryWeaver books keep the publisher's own cover")
            continue
        print(f"{src['id']}: searching")
        # The cover the book had before any picking, so the page can always put it back.
        original = covers.get(src["id"], {}).get("original") or \
            {"fields": cover_fields(src), "image": cover_snapshot(src["id"])}
        covers[src["id"]] = {"original": original,
                             "candidates": commons_candidates(src) + edition_candidates(src)}
        print(f"  {len(covers[src['id']]['candidates'])} candidate(s)")
    WORK.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(covers, ensure_ascii=False, indent=1))
    serve_picker(covers, args.port)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--only")
    b.add_argument("--draft", action="store_true")
    s = sub.add_parser("segment")
    s.add_argument("id")
    s.add_argument("--force", action="store_true", help="replace an existing segments file with a new proposal")
    t = sub.add_parser("text")
    t.add_argument("id")
    r = sub.add_parser("review")
    r.add_argument("id")
    c = sub.add_parser("covers")
    c.add_argument("ids", nargs="*")
    c.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    try:
        {"build": cmd_build, "segment": cmd_segment, "text": cmd_text, "review": cmd_review,
         "covers": cmd_covers}[args.cmd](args)
    except PrepError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
