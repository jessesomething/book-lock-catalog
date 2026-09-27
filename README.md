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
books/<id>/book.json      chapters -> pages (text + optional picture), a quiz per chapter,
                          and ~10-minute segments with a quiz each
books/<id>/*.jpg          cover and page pictures
tools/prep.py             builds books/ and catalog.json from tools/sources.json
tools/sources.json        where each book comes from, plus per-book settings
tools/segments/<id>.json  where each segment starts
tools/quizzes/<id>.json   hand-written quizzes: one list per chapter, one quiz per segment
tools/notes/<id>.md       for long books written across sessions: what each segment covers and
                          which threads are open, so theme questions reach back without spoiling
```

## Adding or rebuilding a book

```sh
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/prep.py build --only <id> --draft   # text + pictures; missing quizzes allowed
.venv/bin/python tools/prep.py segment <id>                # propose segments (or report existing ones)
# move starts inside chapters onto scene breaks, then build --draft again
.venv/bin/python tools/prep.py text <id>                   # chapter and segment text to tools/work/<id>/
# write tools/quizzes/<id>.json and tools/notes/<id>.md, building --draft as you go
.venv/bin/python tools/prep.py review <id>                 # readable quizzes in tools/work/<id>/review.md
.venv/bin/python tools/prep.py build                       # full build; refuses missing quizzes, writes catalog.json
```

A draft `book.json` isn't publishable: restore it (`git restore books/<id>`) before committing
if the book's quizzes aren't finished. Once a book has a segments file, the full build refuses
to run until every segment has its quiz.

## Covers

```sh
.venv/bin/python tools/prep.py covers [<id> ...]   # search, then open the cover picker in the browser
```

The picker shows each book's cover as it is in the app, its original cover, and candidates from
Wikimedia Commons (searched for the title plus "cover" and "first edition") and other English
editions of the same title on Gutenberg. Click one to see it large, drag on it to crop, edit the
credit, and use it. That writes `cover` (the picture's URL), `coverCredit` and `coverCrop` into
the book's lines in `tools/sources.json` and rebuilds the book and `catalog.json`. Putting the
original back restores the file exactly. Commit and push to publish; phones that already have
the book get it via Update on the parent's Books screen.

Commons files whose licence isn't public domain, CC0, CC BY or CC BY-SA are dropped, and so are
landscape pictures. StoryWeaver books are skipped: they keep the publisher's cover. For public
domain, check the artist died more than 70 years ago. Check the credit names who drew the cover:
Commons often lists the author instead, and a Gutenberg edition's credit names its interior
illustrators, who may not have drawn the cover. Search results are cached in
`tools/.cache/`; delete that folder to search again from scratch.

## Segment quizzes

A segment is about 10 minutes of reading, sized at the book's youngest reader's speed; the app
strings segments together into a sitting of whatever length the parent picks. Segments never
end mid-scene: `prep.py segment` avoids cutting before dialogue and leans toward time shifts
("The next morning…"), but its cuts inside chapters still get a skim. Every segment has 3
multiple-choice comprehension questions. Roughly every other segment also has a pair: 1
multiple-choice theme question (themes, motifs, character — it may reach back to earlier
segments) and 1 open written question that goes to the parent and is never graded. The build
requires the pair on the last segment and never lets two segments in a row go without, so any
sitting of two or more segments includes one; the app uses the sitting's most recent pair.

Quizzes are written by hand in Claude Code sessions and read by a person before publishing; no
API calls are involved. Every multiple-choice question carries an `evidence` quote that the build
checks against the text: comprehension evidence must be in its own segment, theme evidence in
that segment or an earlier one. A quote from later in the book is rejected as a spoiler.
Evidence doesn't ship in `book.json`.

Theme questions need one answer the text clearly supports and wrong answers it clearly rules
out. A question a kid could reasonably argue with doesn't belong in a quiz that locks their apps.

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
