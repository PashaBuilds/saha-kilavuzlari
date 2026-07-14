# Chapter 12 — Professional Culture: The Effective Embedded Engineer

In Task 10 you tracked down four defects; this chapter contains no task
card, because the subject at hand is not a skill learned once in a lab but
a habit that settles in a little more each day. What distinguishes a
capable embedded engineer is not working code alone, but the discipline
surrounding that code — writing defensively, keeping it readable, and
communicating effectively with the team.

## Defensive programming: assume that not everything will go as expected

In desktop code, when a function fails it throws an exception, someone
catches it, and execution continues. In embedded systems, that "someone" is
frequently absent — if you do not check, no one does. Three habits form the
foundation of this discipline:

- **Check the return value.** As `_stil.md` emphasizes, the `XST_SUCCESS`
  pattern in this codebase is not decoration; it is a rule. If a driver
  function returns an error code, proceeding to the next line without
  reading that value is a bet that things probably went fine. Building a
  calculation on an I2C register read that failed silently is considerably
  worse than printing an incorrect temperature value to UART knowingly.
- **Make your assumptions visible with `assert`.** If you believe a pointer
  passed into a function will never be NULL, state it explicitly:
  `assert(pDurum != NULL);`. An assert is the cheapest way to say "an
  assumption exists here — report it immediately if it breaks"; it warns
  you early in debug builds and is typically disabled in release builds
  (which is why it complements, rather than replaces, genuine error
  handling).
- **Unbounded waiting without a timeout is not permitted.** In Task 6, you
  were asked to bound the `while` loop waiting for a response from the
  INA226 with a retry limit rather than letting it run indefinitely (add
  this now if it was not already present) — if the hardware fails to
  respond, the program hanging indefinitely is unacceptable. The same
  discipline applies to every hardware wait: do not write "wait until a
  response arrives"; write "wait N attempts or M milliseconds, then return
  an error."

:::tuzak "Working" and "correct" are not the same thing
Observing that code runs successfully once does not mean the code is
correct — it means only that it worked at that moment, under those
conditions. Code left without consideration for what happens when hardware
fails to respond, a cable connection loosens, or a temperature sensor
returns an unexpected value will, sooner or later, encounter one of these
scenarios in the field.
:::

## Code readability and commenting culture

The code itself already states *what* it does — anyone reading a line can
see what a variable holds or how many times a loop executes. The purpose of
a comment is different: to explain **why**, not **what**. A comment like
`i++; /* increment i by one */` wastes time; but a comment like `/* GIC
must be enabled first, otherwise the TTC interrupt never arrives */` saves
the next person (who may well be you, six months later) hours of
rediscovery. The hard lesson from Task 10 resurfaces here: a misleading or
incomplete comment is more dangerous than no comment at all — no comment
can tell a reader that the line claiming "the main loop reads this flag"
may have forgotten `volatile`.

## Version control fundamentals

This is not the place to re-teach the finer points of a Git workflow — you
are already familiar with them from university — but two habits carry
particular weight in embedded work:

- **Small branches, small changes.** The longer a branch lives, the further
  it drifts from the main codebase, and the more painful the eventual
  merge becomes. A peripheral driver, a bug fix — each should remain in its
  own branch, sized to be reviewed on its own.
- **Meaningful commit messages.** Messages like "fix", "wip", or "asdf"
  tell anyone looking at `git log` six months later (including you)
  nothing. A message such as "Fix TTC0 interrupt mask: incorrect bit count
  was doubling the rate" both records your intent at the time and directly
  answers the next person searching for the same bug.

:::ekip-notu Broken builds are never pushed
On our team, there is one non-negotiable rule: the branch you push must
build. A broken build left with the intention of fixing it "later" costs
everyone who pulls that branch afterward a wasted day. Run your local build
one more time before pushing. "Builds but does not work correctly," as in
Task 10, is a different category and less severe — but "does not build" is
never acceptable.
:::

## Submitting code for review

Code being ready for review means more than "done, submitted." Do not skip
these three steps:

- **Prepare a small PR (pull request).** No one can genuinely review an
  800-line change; it gets skimmed and approved, and defects slip through.
  A 100-to-200-line PR serving a single purpose is faster and safer both
  for you and for the reviewer.
- **Review your own code first.** Look through the diff yourself before
  opening the PR. A forgotten `xil_printf` line, test code left commented
  out, a misspelled identifier — catching these yourself lets the reviewer
  spend their time on the logic that actually matters.
- **Follow team style.** The Hungarian notation, `module_object_action()`
  naming, and Allman braces introduced in Chapter 5 are not decorative;
  they are a convention that keeps the entire codebase readable through a
  single lens. A PR that does not follow style is returned with "fix the
  style first," regardless of whether the logic is correct.

:::ekip-notu What to expect from review, and what not to expect
On our team, the purpose of review is to strengthen the code, not to
diminish the author. Receiving a comment is not a reason to become
defensive — the question "why did you do it this way?" is usually genuine
curiosity, not an accusation. The same applies when you are the reviewer:
ask "why is this line here?" rather than stating "this line makes no
sense." Technical disagreement can be rigorous; it should never become
personal.
:::

## A strategy for reading datasheets and user guides

You experienced this firsthand in Task 6: knowing where to begin when
facing a document dozens of pages long is a skill in its own right.
Moreover, a single document is rarely sufficient in embedded work — this
journey has had you working with a triangle of three sources: **UG1271**
describes the board itself (which device connects to which pin), **UG1085**
describes the internals of the chip (register maps, interrupt numbers,
memory addresses), and the device's own datasheet (for example, the
INA226's) describes that device's own register set. The answer to a
problem is rarely found in just one of the three — it is usually found at
the intersection of two: the answer to "which device is this I2C address
assigned to" lies in the board documentation, while the answer to "what
does this register mean" lies in the device datasheet.

Regardless of the document, the reading order stays the same:

1. **Start with the table of contents.** Locate which section holds the
   register map, which holds electrical characteristics, and which holds
   timing diagrams before reading a single line of body text.
2. **Jump to the register summary.** Most datasheets and user guides
   include a "register summary" or "memory map" table; this table is a map
   to the rest of the document.
3. **Return to the body text only when the table is insufficient.** When a
   table alone does not explain the meaning of a field (for example, under
   which condition a given bit is meaningful), go to the relevant
   paragraph — do not attempt to read the document cover to cover; no one
   actually does that.

:::saha-notu Table footnotes are where the real information hides
The habit of skipping the fine-print footnotes beneath a register table is
one of the most costly traps in this profession. Sentences such as "this
bit is valid only when mode X is active" or "the reset value varies by
revision" are precisely what those footnotes contain. When a value behaves
unexpectedly, the first place to check is not the main table — it is the
footnote.
:::

## The art of asking a question: the "what have you tried" template

Chapter 0 stated that asking for help is not a weakness; but how you ask
matters as well. The statement "it's not working, help" forces the other
person to start from zero and repeat work you have already done. Instead,
use a four-part template:

- **Symptom:** What are you observing, precisely? (Not "nothing appears on
  UART," but "the terminal is open, the baud rate is correct, but no
  character has arrived since the board was powered on.")
- **Expected:** What did you expect to happen?
- **Attempts:** Which possibilities have you already ruled out? (Have you
  swapped the cable, tried a different port, confirmed in the debugger
  that the PC reaches `main()`?)
- **Hypothesis:** Where do you suspect the problem lies, if you have a
  guess?

:::ekip-notu Come prepared for "what have you tried"
On our team, responding to a question with "what have you tried" is
standard practice — not to test you, but to avoid duplicating the same
search twice. A question that arrives with the four parts above already
prepared typically gets answered in the second minute rather than the
fifth, because the other person can immediately see where you have not
yet looked.
:::

These habits do not settle in a single day; but now that you know their
names, you will start noticing them — in your own code and in your
teammates' code alike. The technical core of this journey concludes here;
the final stop is a brief tour of concepts beyond the scope of this
document that you will nonetheless encounter by name.
