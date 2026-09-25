# BookLock catalog

Books for [BookLock](https://github.com/jessesomething/book-lock), an Android app where a child
reads a book and passes a short quiz to unlock their other apps for the day. The app reads this
repo over HTTPS: a parent previews books from it and adds them to the child's library, which
downloads them to the phone.

Everything here is openly licensed (CC BY 4.0) or in the public domain. Each book's
`book.json` carries its full credit, licence and a note of what was changed.

## Layout

```
catalog.json              index of every book: metadata, credit, licence, file list, version
books/<id>/book.json      chapters -> pages (text + optional picture), a quiz per chapter
books/<id>/*.jpg          cover and page pictures
tools/prep.py             builds books/ and catalog.json from tools/sources.json
tools/sources.json        where each book comes from, plus per-book settings
tools/quizzes/<id>.json   hand-written quizzes, one list per chapter
```

## Adding or rebuilding a book

```sh
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/prep.py build --only <id> --draft   # text + pictures, no quiz check
.venv/bin/python tools/prep.py text <id>                   # chapter text to tools/work/<id>/ for quiz writing
# write tools/quizzes/<id>.json
.venv/bin/python tools/prep.py build                       # full build; refuses missing quizzes, writes catalog.json
```

StoryWeaver books need their download zip (PDF + attribution file) copied into `sources/`,
which is git-ignored. Page text and pictures on StoryWeaver need a free account to download.

## Licence rules (enforced by `prep.py`)

- Accepted: CC BY 4.0, CC BY-SA 4.0, CC0, public domain. Anything NC or ND is rejected.
- Every book keeps its creators' credit and licence link, and says it was adapted.
- Source platforms' logos and trademarks are not reused; the licence covers the books, not the
  brands.
- Public-domain texts have their distributor's header, footer and name removed. Prefer authors
  who died more than 70 years ago, since public domain differs by country.

## Credits

StoryWeaver books are published by Pratham Books under CC BY 4.0 and first released on
[StoryWeaver](https://storyweaver.org.in). Full per-book and per-illustration credits are in
each `books/<id>/book.json`.
