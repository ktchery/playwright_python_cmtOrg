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
```

The suite runs against the **live production site**, in a visible Firefox window with a
1-second delay between actions so a human can follow along.

> **Note:** `test_contact_page_positive` and `test_contact_page_negative` submit real
> messages through the site's contact form.

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
pytest.ini                 Marker registration (smoke, regression)
```

## Design notes

**Gallery checks use a golden source.** Each hall page asserts against an explicit list of
expected image filenames rather than just counting images, so a photo being swapped or
removed is caught, not just a photo going missing.

**Video checks verify the page, not the provider.** `verify_embedded_video()` first asserts
the expected video is embedded in the page's DOM, and only then checks the embed URL
resolves. Checking reachability alone would pass even if the video were removed from the
site entirely.

**Selectors prefer stable hooks.** Squarespace's accessibility labels have changed over the
site's life (the lightbox arrow's label changed from `Next Item` to `Next`), so gallery
navigation targets component class names instead.

## Known limitations

- The suite targets a third-party Squarespace site, so selectors and the golden image lists
  are coupled to its current markup and will need updating when the site changes.
- It runs headed by design, which means it can't currently run unattended in CI.
