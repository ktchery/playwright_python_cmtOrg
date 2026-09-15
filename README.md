# thecmt.org — UI Test Suite

End-to-end browser tests for [thecmt.org](https://thecmt.org), the site for the Centennial
Memorial Temple's performance spaces. Built with **Playwright** and **pytest** using the
Page Object Model.

The suite covers the pages a visitor actually uses: the three hall pages (Auditorium,
Railton Hall, Mumford Hall) and the contact form — checking that each hall's video is
embedded, that its photo gallery contains the expected images, and that the contact form
both accepts valid submissions and rejects invalid ones with the right error messages.

## Test coverage

| Test | Marker | What it verifies |
|---|---|---|
| `test_home_page_title` | smoke, regression | Home page loads with the expected title |
| `test_navigation_to_auditorium_page` | smoke, regression | Auditorium page resolves at its expected URL |
| `test_auditorium_video` | regression | Auditorium page embeds the expected video and it loads |
| `test_auditorium_images` | regression | All 15 Auditorium gallery images present, in order |
| `test_railton_hall_video` | smoke, regression | Railton Hall embeds the expected video and it loads |
| `test_railton_hall_images` | regression | All 4 Railton Hall gallery images present, in order |
| `test_mumford_hall_video` | smoke, regression | Mumford Hall embeds the expected video and it loads |
| `test_mumford_hall_images` | regression | All 4 Mumford Hall gallery images present, in order |
| `test_contact_page_positive` | smoke, regression | Valid submission returns a confirmation |
| `test_contact_page_negative` | regression | 7 invalid submissions each return the correct validation error |

The negative contact-form cases cover: all fields blank, missing first name, missing last
name, missing email, malformed email, missing subject, and missing message.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install firefox
```

## Running the tests

```bash
pytest                    # full suite (~2 min)
pytest -m smoke           # quick confidence check (5 tests, ~30 s)
pytest -m regression      # full regression set
pytest -v --log-cli-level=INFO   # with live step-by-step logging

HEADLESS=1 pytest         # unattended (~50 s)
HEADLESS=1 SLOW_MO=300 pytest    # headless, with pacing between actions

# What CI runs: everything except the tests that post to the real contact form
HEADLESS=1 pytest -m "not submits_real_form"    # 8 tests, ~30 s

# Mobile: run the same suite against an emulated device
DEVICE="iPhone 13" HEADLESS=1 pytest -m "not submits_real_form"
DEVICE="Pixel 5" BROWSER=chromium HEADLESS=1 pytest
```

The suite runs against the **live production site**. By default it opens a visible Firefox
window with a 1-second delay between actions so a human can follow along; set `HEADLESS=1`
to run it unattended, which is roughly 2.5x faster.

> **Note:** `test_contact_page_positive` and `test_contact_page_negative` submit real
> messages through the site's contact form. There is no staging site, so these carry the
> `submits_real_form` marker and are excluded from every unattended run. Run them
> deliberately, not in a loop.

## Mobile

`DEVICE` runs the whole suite against an emulated device rather than a desktop viewport —
real viewport, user agent, touch support, and device pixel ratio, not just a narrow window:

```bash
DEVICE="iPhone 13" HEADLESS=1 pytest -m "not submits_real_form"
```

Device names come from Playwright's registry (`iPhone 13`, `Pixel 5`, `iPad Mini`, …); an
unrecognised name fails at setup with the valid options rather than silently running
desktop. `BROWSER` overrides the engine when you need it.

All 8 unattended tests pass under iPhone 13 emulation, so the site's mobile layout keeps
the same galleries and video embeds as desktop.

## Self-healing selectors (proposal-only by design)

`heal_selector.py` is the repair half of an AI-assisted test workflow, with the dangerous
half deliberately removed. Given a selector that no longer matches, it inspects the live
page, works out which element that selector used to mean, proposes a more stable
replacement, verifies the proposal resolves, and prints a diff.

**It never edits a test file.**

```bash
python heal_selector.py \
    --url https://thecmt.org/auditorium-2 \
    --selector '//a[@aria-label="Next Item"]' \
    --open '//img[@alt="CMT HouseLeft.png"]' \
    --test-file test_page_classes.py
```

That example is not hypothetical. It is the real breakage in this repo's history: Squarespace
renamed the lightbox arrow's label from `Next Item` to `Next`, which broke three gallery
tests. Run against the pre-fix file from commit `b3cd861^`, the tool proposes
`a.sqs-lightbox-next` — the same fix that was reached by hand.

**How it picks.** Selector words are weighted by how rare they are on the page. In
`//a[@aria-label="Next Item"]` the word that identifies the control is `next`; `item` is
generic UI vocabulary shared with every nav link. Weighting by inverse document frequency
lets the discriminating word decide. Page-level containers are excluded before scoring
rather than merely out-scored — a `<body>` carrying 200 theme classes matches almost any
token by coincidence, which is exactly what the first version of this tool did.

**Why it only proposes.** A healing agent that can rewrite tests can make a failing suite
pass by asserting less: deleting the step it cannot satisfy, or loosening an assertion until
it holds. That is precisely the failure mode this suite was built to catch — three of its
video tests once passed while verifying nothing at all. An agent allowed to commit its own
fixes can recreate that silently and at speed.

So every proposal goes through a human, and any patch that would reduce what a file checks
is rejected outright. `assertion_signature()` compares expect() calls, assert statements and
assertion methods before and after; dropping or weakening any of them fails the guard. That
guard is covered by [`test_heal_selector.py`](test_heal_selector.py) — offline, 7 tests,
including both the obvious cheat (delete the assertion) and the subtle one (swap
`to_have_text` for `to_be_attached`).

## Continuous integration

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs the suite headless on
GitHub Actions, weekly and on manual dispatch — **not** on every push. The target is a
third-party production site belonging to a nonprofit, so hammering it on each commit would
be rude and would tell us nothing new. A scheduled run is the right shape here: it catches
the site drifting out from under the tests, which is the actual failure mode this suite
guards against.

CI deselects `submits_real_form`, so it runs 15 of the 17 tests — 8 browser tests plus the
7 offline unit tests for the healing guard. On failure it uploads the trace, videos, and
screenshots as artifacts.

## Artifacts

Every run produces debugging output, all git-ignored:

- `videos/*.webm` — screen recording of the session
- `trace.zip` — Playwright trace with screenshots, DOM snapshots, and sources.
  View it with `playwright show-trace trace.zip`
- `error_*.png` — screenshot captured at the moment of any test failure

## Project structure

```
test_utility_basepage.py   BasePage — navigation, video verification, test-data helpers
test_page_classes.py       Page objects: HomePage, AuditoriumPage, RailtonHallPage,
                           MumfordHallPage, ContactPage
test_script_main.py        Test cases and Playwright fixtures
heal_selector.py           Proposes replacements for selectors that stopped matching
test_heal_selector.py      Offline tests for the healing guard
pytest.ini                 Marker registration (smoke, regression, unit, submits_real_form)
.github/workflows/         CI: weekly + manual headless run
```

## Design notes

**Gallery checks use a golden source.** Each hall page asserts against an explicit list of
expected image filenames rather than just counting images, so a photo being swapped or
removed is caught, not just a photo going missing.

**Video checks verify the page, not the provider.** `verify_embedded_video()` first asserts
the expected video is embedded in the page's DOM, and only then checks the embed URL
resolves. Checking reachability alone would pass even if the video were removed from the
site entirely.

**The contact form's phone field is optional and unvalidated.** Submitting `abc-not-a-phone`
in it is accepted, so there is no phone validation to assert; the positive test populates it
with a generated number to confirm the optional field is accepted. The adjacent 22px-wide
`autocomplete="new-password"` input is a spam honeypot and is deliberately never filled.

**Device profiles pick their own engine.** Each Playwright device profile names the engine
it emulates, and it matters: iPhone profiles are WebKit, and Firefox rejects them outright
because it does not support `isMobile`. The browser fixture follows the profile rather than
forcing the desktop default, so `DEVICE="iPhone 13"` runs on WebKit — the engine Safari
actually uses — while desktop runs stay on Firefox.

**Selectors prefer stable hooks.** Squarespace's accessibility labels have changed over the
site's life (the lightbox arrow's label changed from `Next Item` to `Next`), so gallery
navigation targets component class names instead.

## Known limitations

- The suite targets a third-party Squarespace site, so selectors and the golden image lists
  are coupled to its current markup and will need updating when the site changes.
- `test_contact_page_negative` is not yet fully reliable headless (roughly 4 runs in 5).
  The contact form is React-rendered and its handlers bind some time after the page loads,
  with no dependable readiness signal; a submission that lands too early is silently
  accepted with no validation banner. `reset_form()` waits for the latest hydration marker
  available, which helps but does not eliminate it. Headed runs are stable because
  `slow_mo` paces the interaction. It is excluded from CI anyway by the
  `submits_real_form` marker, so the flakiness is confined to deliberate local runs. If it
  becomes a problem there: run it headed, or add `pytest-rerunfailures`.
- Mobile coverage reuses the desktop assertions. It confirms the same content and galleries
  work on a phone, but nothing yet asserts mobile-specific chrome such as the hamburger nav.
- Fixtures live in `test_script_main.py` rather than a `conftest.py`, so a second test module
  could not reuse them without moving them first.
