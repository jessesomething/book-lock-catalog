# The Secret Garden — segment notes

What each segment covers and which threads are open, so a later segment's theme question can
reach back without rereading the book, and never forward. Theme evidence must quote this or an
earlier segment; the build rejects anything later.

Sized for age 10 (150 words a minute): 55 segments, 6–16 minutes. Chapter 16 is one segment
(15.8 min): its only scene break comes after 4 minutes.

**Text cleanup** (all in `sources.json`): 374 `[Pg N]` page markers removed with `replace`; the
four verses (two "Mistress Mary" rhymes, the Doxology, "Where you tend a rose") are tables, so
`paragraphs` is `p, table, div.right`; the letters' greeting and signature lines were outside
`<p>`, restored with `replace`. Verse and letter lines get their line breaks from `replace`
(`\n`), because `lineBreaks` only splits on `<br>` and these are table rows. `chapterTitles` fixes
the ten quoted chapter names (`"i Am Colin"` → `"I Am Colin"`) and "Lived In". Dated words about India replaced where the sentence reads the
same (see the report). The big passage in segment 5 (Martha thought Mary would be black; Mary's
"They are not people" outburst) is untouched and left to Jesse; no question uses it.

**Dialect:** Martha, Dickon, Ben and Mrs. Sowerby speak Yorkshire. Evidence quotes keep it;
prompts and choices are plain English.

## Segments

1. **Ch 1.** Mary Lennox in India: sickly, sour, "kept out of the way" by her mother (the Mem
   Sahib) and left to an Ayah who gives her her way; "as tyrannical and selfish a little pig as
   ever lived". Cholera: the Ayah dies, Mary hides in the nursery, drinks wine, sleeps. Wakes to
   silence and a little snake. Officers find her: "the child no one ever saw"; her parents are
   dead.
2. **Ch 2, first part.** Doesn't miss her mother. The clergyman's children (Basil) call her
   "Mistress Mary Quite Contrary" after she sends Basil away from her pretend garden. Sent to her
   uncle Archibald Craven (Basil: "a hunchback, and he's horrid"). Mrs. Crawford: "the most
   unattractive ways"; if her mother had come to the nursery, Mary "might have learned some
   pretty ways". Mrs. Medlock, the housekeeper, meets her in London ("plain little piece of
   goods"). Mary starts to feel lonely; never "any one's little girl".
3. **Ch 2, second part.** Train north with Mrs. Medlock. Captain Lennox (Mary's father) was Mrs.
   Craven's brother; Mr. Craven is Mary's guardian. The house: 600 years old, near a hundred
   rooms, most locked, on the edge of the moor. Mr. Craven has a crooked back; his pretty wife
   died; he cares for nobody, shuts himself in the West Wing, only Pitcher sees him. "Don't go
   wandering and poking about." Rain; Mary sleeps.
4. **Ch 3.** Thwaite Station; Yorkshire speech. Night drive across Missel Moor: wind like the sea;
   "I don't like it." The long house; the dim hall; Pitcher: "He doesn't want to see her", Mr.
   Craven off to London in the morning. Mary kept to two rooms. "Never felt quite so contrary."
5. **Ch 4, Martha.** Tapestry room; the moor from the window. Martha, the chatty Yorkshire
   housemaid, loves the moor. Mary has never dressed herself. Martha thought she'd be black; Mary's
   outburst ("You daughter of a pig"); Mary sobs, lonely, and Martha comforts her. [Sensitive
   passage — no questions on it.]
6. **Ch 4, dressing and breakfast.** White clothes: Mr. Craven won't have a child in black ("Put
   color on her"). "It was the custom." Martha's family: twelve children, sixteen shillings a week;
   Dickon, 12, tames a moor pony, "animals likes him" — Mary's first interest in anyone else
   ("the dawning of a healthy sentiment"). Won't eat her porridge; Martha's siblings are always
   hungry. Sent out to play alone. The locked garden: shut when Mrs. Craven died "so sudden"; key
   buried.
7. **Ch 4, the gardens.** Fountain garden, walled kitchen-gardens, orchard; a wall with no door and
   trees behind it. Ben Weatherstaff (surly gardener) first seen. A robin sings to her from a tree
   over the wall; almost a smile. "People never like me and I never like people." She thinks the
   tree is in the secret garden.
8. **Ch 4, Ben and the robin.** Ben whistles the robin down; it came out of the nest in the
   locked garden, was lonely, befriended Ben — "th' only friend I've got". "I'm lonely," says Mary
   — first time she knows it. Ben: "wove out of th' same cloth… as sour as we look". The robin
   sings to her; she asks it softly to be friends — "like Dickon talks to his wild things". Rose
   trees "ten year' ago"; Ben: no door, don't meddle.
9. **Ch 5.** Days outdoors in the moor wind: Mary gets hungry, eats her porridge ("th' air of th'
   moor"). The neglected ivy at the lower end of the long walk. The robin on the wall; Mary laughs
   and runs after him ("I like you!"). No door anywhere, "but there must have been one ten years
   ago". "The fresh wind from the moor had begun to blow the cobwebs out". Martha tells the story:
   Mrs. Craven's garden, a branch bent like a seat, it broke, she fell and died next day; Mr.
   Craven hates it. Four good things: understood a robin, warm blood, hunger, sorry for someone.
   The crying in the house; Martha says wind, then Betty Butterworth's toothache — Mary doesn't
   believe her.
10. **Ch 6, first part.** Rain. Dickon's fox cub and Soot the crow. Martha's cottage stories:
    fourteen people in four rooms; Mary drawn to "mother" and Dickon. No books; Mary decides to
    explore the hundred rooms and count doors. Nobody minds her; learning to dress herself ("Our
    Susan Ann is twice as sharp"). Portrait gallery; the plain little girl with the green parrot.
11. **Ch 6, second part.** Bedroom with the same girl's portrait; lady's sitting-room with ~100
    ivory elephants; a gray mouse and six babies in a velvet cushion. The crying again, nearer.
    The tapestry door; Mrs. Medlock: "You didn't hear anything of the sort", threatens to lock
    her up. "There was some one crying—there was!"
12. **Ch 7.** Blue sky; spring coming. Martha's day out. "How does tha' like thysel'?" — Mary:
    "Not at all—really." Ben smells spring: crocuses, snowdrops, daffodils, "Tha'll have to wait
    for 'em." Ten years — Mary was born ten years ago. She now likes the robin, Dickon, Martha's
    mother, Martha. The robin follows her; a dog's hole; the old key.
13. **Ch 8, first part.** Mary keeps the key, carries it always; can't find the door under the
    ivy. Martha back: dough-cakes, Dickon says the cottage is fit for a king. Mary offers India
    stories for Martha's family. Mrs. Sowerby (not yet named) worries Mary is alone. The
    skipping-rope, bought for tuppence out of Martha's wages. Mary says thank you, stiffly;
    shakes hands. [Martha's line "No wonder most of 'em's black" is here — flagged, no question.]
14. **Ch 8, second part.** Skipping; Ben: "child's blood in thy veins instead of sour buttermilk";
    twenty skips, then thirty. The robin on the ivy; Mary: "You showed me where the key was".
    "Magic": a gust lifts the ivy, a door knob, the lock; the key turns. She's inside.
15. **Ch 9, first part.** The garden: walls, trees and standard roses tangled in leafless
    climbing roses, gray "hazy mantle"; alcoves, stone seats, urns. "I am the first person who has
    spoken in here for ten years." Dead or alive? Pale green points; she clears grass round them
    with a stick; not lonely at all.
16. **Ch 9, second part.** Two helpings at dinner. Bulbs (Martha): they help themselves, live for
    a lifetime. Mary hides her secret: asks for a spade to make "a little garden"; Martha's mother
    had said give her a bit of her own. Letter to Dickon (seeds and tools, two shillings from
    Mary's purse). Mrs. Sowerby may invite Mary to the cottage. Mary heard the crying a third time;
    Martha runs off.
17. **Ch 10, first part.** A week of sun; bulbs cheer up; Mary skips a hundred, wider awake. Ben:
    "Tha'rt like th' robin"; she's a bit fatter, less yellow. The robin lands on Ben's spade; Ben
    melts. Ben would plant "mostly roses"; learned from a young lady (Mrs. Craven) who loved them;
    she's in heaven; he used to go and prune them once or twice a year, not this year
    (rheumatics). Mary: "I have nothing—and no one." She likes Ben.
18. **Ch 10, second part.** Dickon piping to a squirrel, pheasant and rabbits. Moves slowly so as
    not to startle them. Brought tools and seeds (poppy, larkspur, mignonette). Talks with the
    robin; "p'raps I'm a bird". Asks where her garden is. Mary: "I've stolen a garden…
    Nobody has any right to take it from me when I care about it and they don't," cries, shows
    him. "It's like as if a body was in a dream."
19. **Ch 11, first part.** Dickon: best nesting place in England. "Wick" = alive; green and juicy
    inside means alive; cuts dead wood; "a fountain o' roses here this summer". Mary's clearings:
    "A gardener couldn't have told thee better"; crocuses, snowdrops, narcissus, daffodils. Mary
    stronger; Dickon never catches cold. He'll come every day.
20. **Ch 11, second part.** Keep it wild, not tidy. Dickon: someone has pruned here since it was
    locked (thread — Ben's secret visits, not yet told). "Silver bells": the rhyme; Dickon: no need
    to be contrary with flowers about; Mary stops frowning. She likes five people (Mrs. Sowerby,
    Martha, the robin, Ben, Dickon). "Does tha' like me?" — "I likes thee wonderful." Bread and
    bacon. "Tha' art as safe as a missel thrush."
21. **Ch 12, first part.** "I think he's beautiful!" Martha suggests asking Ben for a corner; Mrs.
    Craven liked Ben. Mr. Craven is back; Mrs. Sowerby stopped him on the moor about Mary; he
    leaves tomorrow till autumn. Mary glad. Mrs. Medlock fetches her; Mary goes stiff and silent.
22. **Ch 12, second part.** Mr. Craven's study: crooked shoulders, miserable face; "I forgot
    you". No governess yet (Mrs. Sowerby's advice). "Might I have a bit of earth?" — reminds him of
    someone who loved growing things (his wife); "take it, child, and make it come alive." Mrs.
    Medlock: liberty and fresh air; Mrs. Sowerby (Susan) and Mrs. Medlock were at school together.
    Dickon gone; a note on a thorn: a missel thrush on a nest, "I will cum bak."
23. **Ch 13, first part.** Martha: the nest drawing means he'll keep her secret. Rainy night; the
    crying; Mary follows it with a candle through the tapestry door. Colin Craven, ivory face, big
    gray eyes with black lashes: "Are you a ghost?" Mr. Craven's son; nobody told either of them.
    Colin won't let people see him; may be a hunchback, "but I shan't live"; his mother died when
    he was born; father can't bear to see him. Iron brace; the London doctor said fresh air; Colin
    hates fresh air.
24. **Ch 13, second part.** Colin gets anything he wants; "no one believes I shall live". Both are
    ten — the garden was locked when he was born. Colin wants to make them open it; Mary panics
    (Dickon would never come back); a secret garden, "our nest", maybe a boy to push his chair.
    Mary sees Colin is spoiled — and hadn't known she was. Dr. Craven is his father's cousin and
    would inherit. "I should not mind fresh air in a secret garden."
25. **Ch 13, third part.** Mary describes the garden; the robin makes Colin smile, "almost
    beautiful". The portrait behind the silk curtain: his mother, with his eyes; "Sometimes I
    hate her for doing it" (dying). Mary to be his secret too; Martha has known all along (nurse
    away). Mary sings a Hindustani song, strokes his hand; he sleeps.

26. **Ch 14, first part.** Rain. Mary tells Martha she found Colin; Martha fears losing her place.
    "Tha' must have bewitched him." Martha on Colin: Mr. Craven wouldn't look at the baby; they
    kept him lying down, a brace; the London doctor: too much medicine, too much of his own way;
    fevers; Mrs. Medlock said he'd die. Mary: a garden might do him good. The "rose cold"
    tantrum. Colin sends for Mary.
27. **Ch 14, second part.** Colin orders Martha not to worry ("I'll take care of you"). Mary: like a
    boy Rajah in India; different from Dickon. The moor through Dickon's eyes. "I am going to
    die" — Mary won't sympathize; Dr. Craven (cousin, would inherit) looks cheerful when he's worse.
    The London doctor: "The lad might live if he would make up his mind to it." "Let us talk about
    living." They laugh; "We are cousins." Dr. Craven and Mrs. Medlock walk in; Colin: "She makes
    me better." Tea together.
28. **Ch 15, first part.** A week of rain with Colin; no tantrums since (Mrs. Medlock). Mary tests
    whether Colin can be trusted; she's changed (less yellow, hair thicker). Colin bit a lady who
    pitied him. He wouldn't mind Dickon: "a boy animal".
29. **Ch 15, second part.** First blue morning: Mary out at dawn; "Six months before… she missed
    nothing." Dickon already there with Captain (fox) and Soot (crow); crocuses; Mary kisses them.
    Leaf-buds on "dead" roses.
30. **Ch 15, third part.** The robin building a nest — keep still. Mary tells Dickon about Colin;
    Dickon relieved (dislikes hiding things); his mother lets him keep secrets. Colin's eyes like
    his mother's; Mr. Craven wishes he'd never been born — "Them as is not wanted scarce ever
    thrives." The green veil on the walls. Plan: bring Colin out, Dickon pushing the chair.
31. **Ch 16 (whole).** Mary skips Colin for the garden. Dickon: stronger, "beginning to look
    different". Colin sulks; the fight: "You are a selfish thing!" "Mr. Rajah!" Dickon "like an
    angel"; "You just say that to make people sorry"; pillow thrown; "I won't come back!" The nurse
    laughs: someone to stand up to him at last. Mr. Craven's gifts (books, garden books, games,
    gold writing-case). Colin's secret fear of the lump. Mary decides she might go back.
32. **Ch 17, first part.** Night tantrum; the nurse fetches Mary; she storms in: "I hate you!…
    just hysterics!" Colin stops; she examines his back: "not a lump as big as a pin".
33. **Ch 17, second part.** Most of his illness "created by himself"; the nurse agrees there's no
    lump; "Do you think—I could—live to grow up?" — fresh air, no temper. Making up; he'll go out if
    Dickon pushes. Mary hints she's found the way in; tells him the garden till he sleeps.
34. **Ch 18.** Colin says "please". Mrs. Sowerby: worst things are never having your own way — or
    always having it. Nut and Shell (squirrels), Jump (pony). Dickon: "we munnot lose no time".
    Mary speaks Yorkshire; Colin laughs; Mrs. Medlock amazed. Colin wishes he were friends with
    things; "I even like you." Colin sorry about Dickon. Mary trusts him: the door under the ivy;
    she's been inside for weeks. [Frontispiece plate shows this chapter's garden scene; it's
    before chapter 1 in the edition, so dropped.]
35. **Ch 19, first part.** Dr. Craven finds Colin laughing over garden books with Mary; wants
    fresh air; "a very strong boy" (Dickon) will push — Dr. Craven relieved; no bromide; "my cousin
    makes me forget". Mrs. Medlock: Susan Sowerby says "children needs children", and the whole
    orange: "th' whole orange doesn't belong to nobody… no sense in grabbin' at th' whole orange".
36. **Ch 19, second part.** Colin sleeps well; Mary bursts in: "It has come, the Spring!" Window
    open, long breaths. The motherless lamb. Breakfast for two; Colin orders the animals brought
    up. Dickon arrives with lamb, fox, crow, squirrels (plate 2 here); feeds the lamb; the lamb
    story; columbines in the garden book. "Tha' munnot lose no time."
37. **Ch 20, first part.** A week's wait (wind, a cold). Planning the secret route. Mr. Roach, the
    head gardener, summoned: no one near the Long Walk at 2 o'clock. "You have my permission to
    go." Mrs. Medlock: Mary may teach him "the whole orange does not belong to him." Colin has
    never really seen spring.
38. **Ch 20, second part.** Carried down by the strongest footman; Dickon pushes; gorse scent;
    Mary shows the places (robin, key, ivy). Colin covers his eyes until inside; the green veil,
    blossom; a pink glow over him: "I shall get well!… forever and ever and ever!"
39. **Ch 21, first part.** The perfect afternoon; the plum-tree canopy; Colin tries Yorkshire.
    The old dead tree with a broken branch (where Mrs. Craven fell — Mary and Dickon hide it; the
    robin distracts Colin — "Magic"). Dickon: his mother thinks Mrs. Craven may be about, looking
    after Colin. Colin's color stays. Tea and crumpets.
40. **Ch 21, second part.** "I'm going to grow here myself." Colin's legs: nothing wrong, just
    weak and afraid. Ben on a ladder over the wall, furious at Mary; Colin wheeled up: "Do you know
    who I am?" Ben: "tha' mother's eyes… th' poor cripple." "I'm not a cripple!" Anger lifts him;
    Colin stands. Ben weeps: "Tha'lt make a mon yet." Colin orders him into the secret.
41. **Ch 22.** Dickon: "Tha's doin' Magic thysel'." Colin walks to a tree; Mary's chant "You can
    do it!" Ben: "Tha's got too much pluck". Ben kept on because Mrs. Craven liked him; it was her
    garden; Ben climbed the wall once a year to prune (resolves the pruning thread) — she'd asked
    him to care for her roses. Colin digs; plants a rose from the greenhouse before sunset;
    standing, laughing.
42. **Ch 23, first part.** Dr. Craven worried; Colin: "It would not be wise to try to stop me."
    Mary: sorry for Dr. Craven, having to be polite to a rude boy; "always having your own way…
    made you so queer" — she was the same. "Good Magic… white as snow." The months of bloom (Ben
    made earth pockets in the walls for her). Colin watches things grow; decides on an experiment.
43. **Ch 23, second part.** Colin's "scientific" lecture on Magic: Ben ("Aye, aye, sir" — ran away
    to sea as a boy), Dickon, Mary in a row. Magic makes things out of nothing; it made him stand;
    chant "Magic is in me!" daily. [Ben's Jem Fettleworth anecdote — a drunk husband beating his
    wife, played for laughs — flagged; no question on it.] Dickon: "It'll work."
44. **Ch 23, third part.** The circle cross-legged under the tree, animals join; Colin chants; Ben
    dozes. The procession round the garden; Colin walks, resting. Secret from everyone until he
    can walk and run — then he'll walk into his father's study. "More than half the battle."
    Wants to be an athlete; scolds Ben for "prize-fighter".
45. **Ch 24, first part.** Dickon's cottage garden ("be friends with 'em for sure"). Mrs. Sowerby
    told the whole secret: "th' makin' o' her an' th' savin' o' him." The play-acting (groaning to
    throw people off). Laughing better than pills. Their hunger; she'll send milk and buns.
46. **Ch 24, second part.** Nurse and Dr. Craven notice his appetite; Colin forbids writing to his
    father. Can't eat less; "not enough for a person who is going to live". Milk and currant buns
    from the pails; Colin: Mrs. Sowerby "is a Magic person". They send shillings for food.
47. **Ch 24, third part.** Oven in the hollow: roast eggs and potatoes. Bob Haworth's exercises via
    Dickon. They leave their meals untouched; Mrs. Medlock baffled; Dr. Craven: "The boy is a new
    creature." Mary "downright pretty". "Let them laugh."
48. **Ch 25, first part.** The robin's view: Eggs; Dickon speaks robin; the boy on wheels was
    suspicious; decides Colin is learning to walk as birds learn to fly (short flights and rests);
    the exercises puzzle him.
49. **Ch 25, second part.** Rainy day: Colin can't keep still, wants his father home. Exploring the
    hundred rooms; running in the gallery; the parrot girl (Colin's ancestor, like old Mary); the
    elephants; the empty mouse hole. Huge lunch. The curtain now open: her laughing no longer
    angers him; "If I were her ghost—my father would be fond of me."
50. **Ch 26, first part.** Magic lectures; Ben watches Colin fill out ("three or four pound").
    Colin: "I'm well! I'm well!" Ben suggests the Doxology; Dickon sings; all sing; Ben weeps again
    (plate 3 here). "Gone up five pound."
51. **Ch 26, second part.** Mrs. Sowerby comes in (Dickon told her the door). "Eh! dear lad!" — so
    like his mother. His father "mun come home". Mary will be "like a blush rose". Magic = "th' Big
    Good Thing", the name doesn't matter. Feast; plans to visit the cottage. "I wish you were my
    mother." "Thy own mother's in this 'ere very garden, I do believe."
52. **Ch 27, first part.** Thoughts are as powerful as batteries; Mary and Colin changed by new
    thoughts; "Where you tend a rose, my lad, / A thistle cannot grow." Mr. Craven's ten years of
    dark thoughts, wandering Europe. By a stream in the Tyrol, blue forget-me-nots; he feels alive
    — the same day Colin cried "forever and ever".
53. **Ch 27, second part.** The calm comes and goes; Lake Como; sleeping better. Dream: "Archie!…
    In the garden!" (Lilias = his wife, not named as such). Susan Sowerby's letter: come home. He
    goes at once.
54. **Ch 27, third part.** The journey: memories of refusing the baby; "Perhaps I have been all
    wrong"; "too late" is the wrong Magic. The Sowerby cottage: mother away helping with a new
    baby; a sovereign for the children. The moor feels like home. Mrs. Medlock baffled: "In the
    garden, sir."
55. **Ch 27, fourth part.** The Long Walk; laughter inside; Colin races out into his arms: "Father,
    I'm Colin." The garden in autumn; "I thought it would be dead." The whole story. Colin walks
    back beside his father; Ben and the servants see them cross the lawn.

## Theme and written pairs

34 segments carry the pair: 1, 2, 4, 6, 8, 9, 11, 12, 14, 16, 18, 20, 22, 23, 25, 27, 29, 30, 31,
33, 34, 35, 37, 38, 40, 41, 42, 44, 46, 48, 50, 52, 54, 55. No two in a row go without.

## Threads (all resolved by the end)

- The pruning in the locked garden: Ben, over the wall, for Mrs. Craven (seg 41).
- Colin's fear of a hunch and of dying: no lump (32), stands (40), "I'm well" (50).
- Mr. Craven: away (22) → "coming alive" in the Tyrol (52) → home (55).
- Mrs. Sowerby: advice all through; first seen in person in seg 51.
