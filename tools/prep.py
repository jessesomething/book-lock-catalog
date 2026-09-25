#!/usr/bin/env python3
"""Build the BookLock catalog from tools/sources.json.

    python tools/prep.py build [--only ID] [--draft]
    python tools/prep.py text ID        # dump chapter text to tools/work/ID/ for quiz writing

--draft skips the quiz check so text can be extracted before quizzes exist.
Drafts are never valid for publishing: catalog.json is only written on a full build.
"""
import argparse
import hashlib
import io
import json
import re
import sys
import urllib.request
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
        req = urllib.request.Request(url, headers={"User-Agent": "BookLock catalog prep"})
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


def paginate(paragraphs, page_words):
    pages, current, count = [], [], 0
    for p in (part for para in paragraphs for part in split_long(para, page_words)):
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
        save_image(fetch(base + src["cover"]), out_dir / "cover.jpg", src.get("coverCrop"))
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
        chunks = paginate(paras, page_words) or [""]
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
    return [{"title": c["title"], "pages": [{"text": t, "image": None} for t in paginate(c["paras"], page_words)]}
            for c in chapters]


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
    # "evidence" is for human review only; it doesn't ship in book.json.
    return [[{k: q[k] for k in ("prompt", "choices", "correctIndex")} for q in quiz]
            for quiz in quizzes[:chapter_count]]


def build_book(src, draft):
    out_dir = BOOKS / src["id"]
    if out_dir.exists():
        for f in out_dir.iterdir():
            f.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    builder = {"storyweaver": build_storyweaver, "gutenberg": build_gutenberg}[src["source"]]
    book = builder(src, out_dir)

    if book["licence"] not in ALLOWED_LICENCES:
        raise PrepError(f"{src['id']}: licence {book['licence']!r} is not allowed")

    genre = src.get("genre")
    if genre not in GENRES:
        raise PrepError(f"{src['id']}: genre {genre!r} must be one of {GENRES}")

    quizzes = load_quizzes(src["id"], len(book["chapters"]), draft)
    for chapter, quiz in zip(book["chapters"], quizzes):
        chapter["quiz"] = quiz

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
        "imageCredits": book["imageCredits"],
        "changes": book["changes"],
        "wordCount": words,
        "chapters": book["chapters"],
    }
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
        entries.append(catalog_entry(book_json, src.get("starter", False)))
    (ROOT / "catalog.json").write_text(json.dumps(
        {"formatVersion": FORMAT_VERSION, "books": entries}, ensure_ascii=False, indent=1))
    print(f"catalog.json: {len(entries)} books")


def cmd_text(args):
    book = json.loads((BOOKS / args.id / "book.json").read_text())
    out = WORK / args.id
    out.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(book["chapters"], 1):
        body = "\n\n".join(p["text"] for p in c["pages"])
        (out / f"ch{i:02d}.txt").write_text(f"{c['title'] or book['title']}\n\n{body}\n")
    print(f"wrote {len(book['chapters'])} chapter files to {out.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--only")
    b.add_argument("--draft", action="store_true")
    t = sub.add_parser("text")
    t.add_argument("id")
    args = parser.parse_args()
    try:
        {"build": cmd_build, "text": cmd_text}[args.cmd](args)
    except PrepError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
