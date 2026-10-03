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
guard is covered by [`test_heal_selector.py`](test_heal_selector.py) — offline, 8 tests,
including both the obvious cheat (delete the assertion) and the subtle one (swap
`to_have_text` for `to_be_attached`).

## API layer

[`test_api.py`](test_api.py) checks the site over HTTP with no browser: 42 tests in about
6 seconds. It answers one question — is the site up, serving the right pages, and will a
visitor get a working experience?

```bash
pytest -m api                 # 42 tests, ~6 s, no browser
pytest -m "api or unit"       # everything that needs no browser, ~9 s
```

Squarespace serves structured data for any page by appending `?format=json`, and that is
where most of these assertions live. Page titles, url ids and video references sit in real
structured fields that survive a reskin — which matters, because both of this suite's worst
defects came from testing generated markup.

**Every path, title, video id and gallery filename is imported from the page objects.**
Nothing is re-typed. That is not tidiness: the site also serves `/auditorium`,
`/mumford-hall` and `/contact`, which all return 200 but are *different pages* from the ones
the UI suite covers. Hardcoding the plausible-looking name would test the wrong page and
still report green.

What it covers: route liveness and content type, `http` → `https` redirect, page identity
(`collection.title` / `urlId`), site title, the video reference each page declares, whether
every one of the 23 golden-source gallery images actually loads, the video host as its own
deliberate test, real 404s on unknown paths, and the contact page still declaring its form
block.

**One honest limit.** Titles, url ids and video references are structured JSON and genuinely
immune to HTML drift. Gallery images are not — they appear only inside
`collection.collections[0].mainContent`, a ~65KB blob of generated markup. So the gallery
tests here do not assert on that markup at all. They fetch the images and check they return
200 and an image content type, which no reskin can fake and which the UI suite never
checked: it asserts a `data-src` attribute is present, and that stays true after the asset
behind it disappears.

**The contact form endpoint is not tested, for narrower reasons than first assumed.** An
instrumented run — every POST aborted at the network layer — established that validation is
**server-side**: a blank submission to `/api/form/SaveFormSubmission` returns HTTP 400 with a
JSON error body and creates nothing. An earlier version of this section claimed a negative API
test would be unsafe because validation was client-side only. That was wrong, and the
experiment disproved it.

It stays out because a *valid* submission would create a real enquiry in a real nonprofit's
inbox, so the happy path cannot be tested here at all; and the negative path needs a submission
key fetched per request, buying a brittle test for behaviour the UI suite already covers from
the user's side. The input fields are not in the served HTML either — React builds them — so
the API layer asserts the form block still exists and leaves the rest to the UI tests.

Also skipped as unfalsifiable noise: `robots.txt` contents, the favicon, the `server` header,
JSON payload sizes, and response-time budgets.

## Continuous integration

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs the suite headless on
GitHub Actions, **monthly and on manual dispatch — never on push**.

The cadence is a deliberate trade. The target is a third-party production site belonging to
a nonprofit, with no staging environment, so monthly works out to roughly 12 runs a year at
8 page loads each — about a hundred page views annually, indistinguishable from someone
browsing the site occasionally. Weekly or per-push would be a visible, unexplained pattern
of browser sessions against a server we do not operate.

There is a schedule at all because this suite exists to catch the site drifting out from
under the tests, and drift is exactly what a manual run cannot find — it went unnoticed here
for two years. Monthly is slow enough to be polite and often enough to catch it.

Failures arrive by email through GitHub's own Actions notifications (Settings →
Notifications → Actions → "failed workflows only"); no mail service or secrets required.

CI deselects `submits_real_form`, so it runs 58 of the 60 tests — 8 browser tests, 42 API
tests, and 8 offline unit tests for the healing guard. On failure it uploads the trace, videos, and
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
test_script_main.py        Browser test cases and Playwright fixtures
test_api.py                Browserless HTTP and ?format=json checks
conftest.py                The shared Playwright instance both layers need
heal_selector.py           Proposes replacements for selectors that stopped matching
test_heal_selector.py      Offline tests for the healing guard
pytest.ini                 Markers (smoke, regression, api, unit, submits_real_form)
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
- `test_contact_page_negative` is not fully reliable headless (roughly 4 runs in 5), and
  **the cause is not established**. Measured: the test is flaky headless and stable headed,
  and waiting on the `react-form-contents` marker in `reset_form()` raised the pass rate from
  about 1 in 2 to about 4 in 5 — though whether that is genuine readiness or simply added
  delay is unknown. An earlier version of this note blamed a hydration race in which an early
  submit posted silently past client-side validation. An instrumented run disproved it: a
  blank submission POSTs to `/api/form/SaveFormSubmission` whether or not the form has
  hydrated, and the server rejects it with HTTP 400 and a JSON error body. Validation is
  server-side. The failing runs show the banner absent, not a submission getting through.
  Excluded from CI by the `submits_real_form` marker either way. If it becomes a problem
  locally: run it headed, or add `pytest-rerunfailures`.
- Mobile coverage reuses the desktop assertions. It confirms the same content and galleries
  work on a phone, but nothing yet asserts mobile-specific chrome such as the hamburger nav.
- Only the shared Playwright instance moved to `conftest.py`; the browser and device fixtures
  still live in `test_script_main.py`. A third module needing a browser would want those moved
  too.
