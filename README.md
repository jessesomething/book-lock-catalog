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
tools/shelf.html          the page for picking new books (`prep.py shelf`)
tools/sources.json        where each book comes from, plus per-book settings
tools/segments/<id>.json  where each segment starts
tools/quizzes/<id>.json   hand-written quizzes: one list per chapter, one quiz per segment
tools/notes/<id>.md       for long books written across sessions: what each segment covers and
                          which threads are open, so theme questions reach back without spoiling
```

## Finding new books

In the app repo, `/add-books` runs the whole process. It asks what to look for, writes
candidates to `tools/work/shelf/candidates.json` (with a synopsis, themes, genre and ages for
each), and opens a page to pick from:

```sh
.venv/bin/python tools/prep.py shelf     # look up each candidate and open the page to pick them
.venv/bin/python tools/prep.py add       # add the picked books to sources.json
.venv/bin/python tools/prep.py status    # where every book stands, from source to published
```

The page shows each candidate's Open Library rating and a popular edition's cover. It also shows
the length, number of pictures and reading time of the Gutenberg edition. It warns when that
edition's title doesn't match, or when any author, illustrator or translator died less than 70
years ago (going by Gutenberg's catalog). Pressing Add writes `tools/work/shelf/picks.json` and
stops the page.

Several books can then be prepped and quizzed side by side, one agent per book. Agents change
`sources.json` only through `prep.py set <id> '{"key": value}'` (null removes a key), which
edits that book's lines under a lock. They build only with `--only <id> --draft`, because a full
build rewrites `catalog.json`.

## Adding or rebuilding a book

```sh
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/prep.py build --only <id> --draft   # text + pictures; missing quizzes allowed
.venv/bin/python tools/prep.py segment <id>                # propose segments (or report existing ones)
# move starts inside chapters onto scene breaks, then build --draft again
.venv/bin/python tools/prep.py text <id>                   # chapter and segment text to tools/work/<id>/
# write tools/quizzes/<id>.json and tools/notes/<id>.md, building --draft as you go
.venv/bin/python tools/prep.py review <id>                 # judgment calls to read, in tools/work/<id>/review.md
.venv/bin/python tools/prep.py review <id> --all           # ... plus every comprehension question
.venv/bin/python tools/prep.py build                       # full build; refuses missing quizzes, writes catalog.json
```

Each `catalog.json` entry has a `version` (any file changed) and `parts`, a fingerprint each
for the cover, text, pictures, quizzes and credits. The app compares `parts` with the copy on the
phone to say what an update changes.

Gutenberg chapter books start a chapter at each `h2` reading "CHAPTER …", and take its name from
an `h3` right after it. Editions that mark chapters differently set CSS selectors in
`sources.json`: `headings`, `names`, and `paragraphs` for text in something other than `<p>`
(for example Alice: `div.chapter`, `div.sidenote`, `p, div.unindent`). `"lineBreaks": true`
keeps each `<br>` as a line break, for books with verse, and `"chapterTitles": {"2": "The Pool
of Tears"}` renames a chapter whose name comes out wrong. A picture inside a
chapter starts a page that holds about half the usual words. Pictures narrower than 250px are
treated as decoration (drop capitals, emblems) and left out. A book with segments needs no
chapter quizzes: the app quizzes segments, and falls back to chapter quizzes only for copies
downloaded before segments existed.

Passages cut for content go in `"cuts"`, not `skipParagraphs`: a list of
`{"note": ..., "paragraphs": [...], "replace": {...}}`, one per passage. The note is a short line
for parents. The build leaves the cut out of `text`, and a page with a cut also carries its
`original` wording and `cutNotes`. Parents who turn on "Keep passages cut from older books" see the
original in the reader, and a notice in Parent settings before the kid's next reading reaches one.
Quizzes, segments and word counts always use the cut text, so no question can depend on a cut.
Cuts work in chapter books only, and a paragraph with a cut must fit on one page.

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
the book's lines in `tools/sources.json` and rebuilds the book: a published book in full, along
with its `catalog.json` entry, and a book still being written as a draft. `/covers` in the app
repo runs this. Putting the
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
API calls are involved. The person reads the judgment calls: theme, link and written questions,
which is what `prep.py review` shows. Comprehension questions are left to the build's evidence
check, with `review --all` for a spot-check. Every multiple-choice question carries an `evidence` quote that the build
checks against the text: comprehension evidence must be in its own segment, theme evidence in
that segment or an earlier one. A quote from later in the book is rejected as a spoiler.
Evidence doesn't ship in `book.json`.

A segment with a theme question may also have a `link` question: one that ties what was just read
to an earlier part of the book ("Who else has Dorothy helped along the way?"). It names the
earlier segments it draws on in `from` (1-based, as in `review.md`), and its evidence needs a quote
of at least 4 words from each of them and from its own segment. The app asks it instead of the
theme question when the kid has passed those segments, and falls back to the theme question when
they haven't (one was sent back to be reread and isn't passed yet). Link questions are optional extras: about one per
chapter, at a segment that ends a chapter, from the third segment on. Oz has them; a book
doesn't wait for them.

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
