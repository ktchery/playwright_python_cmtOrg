"""API-layer tests for thecmt.org.

Browserless checks that answer one question: is the site up, serving the right
pages, and will a visitor get a working experience? They run in a couple of
seconds, so they can be the first thing that fails and the cheapest signal that
something is wrong.

Every path, title, video id and gallery filename here is imported from the page
objects in test_page_classes.py. Nothing is re-typed: if a URL changes there,
these tests follow it rather than quietly disagreeing with the UI suite.

WHAT IS DELIBERATELY NOT TESTED HERE

- The contact form endpoint, /api/form/SaveFormSubmission. An instrumented run
  (POSTs aborted at the network layer) established that validation is
  server-side: a blank submission returns HTTP 400 with a JSON error body, and
  creates nothing. So a NEGATIVE API test would in fact be safe - an earlier
  note here claimed the opposite, reasoning from a client-side-validation
  assumption that turned out to be wrong.

  It is still left out, for two narrower reasons. A valid submission would
  create a real enquiry in a real nonprofit's inbox, so the happy path cannot be
  tested here at all. And the negative path needs a submission key fetched per
  request, which buys a brittle test for behaviour the UI suite already covers
  from the user's side. If that changes, the safety argument no longer blocks
  it; only the cost-benefit does.
- robots.txt contents, the favicon, the `server` header, JSON payload sizes, and
  the shoppingCart / shareButtons / localizedStrings keys. All present, none
  connected to whether a visitor can use the site. A test that cannot fail in a
  way anyone cares about is noise in the report.
- Response-time budgets. No stable baseline, and a slow CI runner would fail a
  healthy site.

ONE HONEST LIMIT: page titles, urlIds and video references live in structured
JSON fields and genuinely do not move when Squarespace reskins its HTML.
Gallery images do not - they appear only inside collection.collections[0]
.mainContent, a ~65KB blob of generated markup. So the gallery check here does
not assert on that markup at all; it asserts the images themselves still load,
which no amount of reskinning can fake and which the UI suite never checked.
"""

import json

import pytest

from test_page_classes import (
    AuditoriumPage,
    ContactPage,
    HomePage,
    MumfordHallPage,
    RailtonHallPage,
)
from test_utility_basepage import BasePage

SITE = "https://thecmt.org"

# The form block the contact page is built around. Public in the page source;
# asserted so the form going missing is a test failure rather than a silent
# loss of the site's only contact route.
CONTACT_FORM_ID = "5e30504775f9761f1052d3a4"

# (label, path, expected collection.title, expected collection.urlId)
# Paths are derived from the page objects, never re-typed. This matters: the
# site also serves /auditorium, /mumford-hall and /contact, which return 200 but
# are different pages from the ones the UI suite covers. Hardcoding the
# plausible-looking name would test the wrong page and still go green.
PAGES = [
    ("home", HomePage.HOME_URL.replace(SITE, "") or "/", "Home", "home-2"),
    ("auditorium", AuditoriumPage.AUDITORIUM_URL.replace(SITE, ""), "Auditorium", "auditorium-2"),
    ("railton", RailtonHallPage.RAILTON_HALL_URL.replace(SITE, ""), "Railton Hall", "railton-hall"),
    ("mumford", MumfordHallPage.MUMFORD_HALL_URL.replace(SITE, ""), "Mumford Hall", "new-index-1"),
    ("contact", ContactPage.CONTACT_URL.replace(SITE, ""), "Contact", "new-index"),
]

# Pages that embed a video, with the id the UI suite also expects.
VIDEO_PAGES = [
    ("auditorium", AuditoriumPage.AUDITORIUM_URL.replace(SITE, ""), AuditoriumPage.VIDEO_ID),
    ("railton", RailtonHallPage.RAILTON_HALL_URL.replace(SITE, ""), RailtonHallPage.VIDEO_ID),
    ("mumford", MumfordHallPage.MUMFORD_HALL_URL.replace(SITE, ""), MumfordHallPage.VIDEO_ID),
]

# Every golden-source gallery image, as one flat list of CDN URLs.
GALLERY_ASSETS = [
    (f"{label}/{path.rsplit('/', 1)[-1]}", f"{BasePage.CDN_BASE}/{path}")
    for label, cls in [
        ("auditorium", AuditoriumPage),
        ("railton", RailtonHallPage),
        ("mumford", MumfordHallPage),
    ]
    for path in cls.GALLERY_IMAGES
]

pytestmark = pytest.mark.api


@pytest.fixture(scope="session")
def api(playwright_instance):
    """A browserless request context.

    Shares the session's Playwright instance (see conftest.py) rather than
    opening its own - a second sync_playwright() in one process fails. It does
    not touch playwright_browser or playwright_context, so no browser is
    launched for these tests and the UI fixtures keep their own job.
    """
    context = playwright_instance.request.new_context(base_url=SITE)
    yield context
    context.dispose()


def page_json(api, path):
    """Squarespace serves structured data for any page via ?format=json."""
    response = api.get(f"{path}?format=json")
    assert response.ok, f"{path}?format=json returned {response.status}"
    return json.loads(response.body())


# --------------------------------------------------------------------------
# Is the site up? Seconds to run, and the first thing worth knowing.
# --------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.parametrize("label,path,_title,_urlid", PAGES, ids=[p[0] for p in PAGES])
def test_page_is_served(api, label, path, _title, _urlid):
    response = api.get(path)
    assert response.status == 200, f"{path} returned {response.status}"
    assert "text/html" in response.headers.get("content-type", ""), (
        f"{path} served {response.headers.get('content-type')!r}, not HTML"
    )


@pytest.mark.smoke
def test_http_redirects_to_https(api):
    """A broken redirect makes a live site look dead, and silently downgrades
    every visitor who types the bare domain."""
    response = api.get("http://thecmt.org", max_redirects=0)
    assert response.status == 301, f"expected a 301, got {response.status}"
    assert response.headers.get("location", "").startswith("https://"), (
        f"redirects to {response.headers.get('location')!r}, not https"
    )


@pytest.mark.smoke
def test_contact_page_still_declares_its_form(api):
    """The form is the site's only conversion path, so its disappearance matters.

    This asserts the page still declares the form block and its id - not that
    the input fields exist. The inputs are built by React in the browser and are
    absent from the served HTML entirely, so there is nothing to assert against
    at this layer. The fields are the UI suite's job. Nothing here submits.
    """
    data = page_json(api, ContactPage.CONTACT_URL.replace(SITE, ""))
    blob = data["collection"]["collections"][0]["mainContent"]
    assert "sqs-block-form" in blob, "contact page no longer declares a form block"
    assert CONTACT_FORM_ID in blob, (
        f"contact page no longer references form {CONTACT_FORM_ID}"
    )


# --------------------------------------------------------------------------
# Is it serving the right pages? Structured fields, stable across reskins.
# --------------------------------------------------------------------------

@pytest.mark.regression
@pytest.mark.parametrize("label,path,title,urlid", PAGES, ids=[p[0] for p in PAGES])
def test_page_identity(api, label, path, title, urlid):
    """Catches a page being renamed, replaced, or swapped for a near-duplicate -
    the failure that makes /auditorium and /auditorium-2 easy to confuse."""
    data = page_json(api, path)
    collection = data["collection"]
    assert collection["title"] == title, (
        f"{path} reports title {collection['title']!r}, expected {title!r}"
    )
    assert collection["urlId"] == urlid, (
        f"{path} reports urlId {collection['urlId']!r}, expected {urlid!r}"
    )


@pytest.mark.regression
def test_site_title(api):
    data = page_json(api, "/")
    assert data["website"]["siteTitle"] == "THECMT"


@pytest.mark.regression
@pytest.mark.parametrize("label,path,video_id", VIDEO_PAGES, ids=[p[0] for p in VIDEO_PAGES])
def test_video_is_referenced_by_the_page(api, label, path, video_id):
    """The stable half of the fix for tests that checked YouTube instead of the
    site. This asserts the page itself still claims the video; whether the host
    is up is a separate test, below, whose job that is."""
    data = page_json(api, path)
    url = data["collection"]["collections"][0]["video"]["url"]
    assert video_id in url, f"{path} references {url!r}, expected id {video_id}"


# --------------------------------------------------------------------------
# Will a visitor actually get a working page?
# --------------------------------------------------------------------------

@pytest.mark.regression
@pytest.mark.parametrize("name,url", GALLERY_ASSETS, ids=[a[0] for a in GALLERY_ASSETS])
def test_gallery_image_loads(api, name, url):
    """A gallery of broken images looks broken to a visitor, and the UI suite
    cannot catch it: it asserts the data-src attribute is present, which stays
    true after the asset behind it disappears."""
    response = api.get(url)
    assert response.status == 200, f"{name} returned {response.status}"
    assert response.headers.get("content-type", "").startswith("image/"), (
        f"{name} served {response.headers.get('content-type')!r}, not an image"
    )


@pytest.mark.regression
def test_video_host_is_reachable(api):
    """Deliberately its own test. Three tests used to check this *instead of*
    the page and reported green with the video removed from the site. The check
    is legitimate - it just has to be honest about what it covers."""
    response = api.get(f"https://www.youtube.com/embed/{AuditoriumPage.VIDEO_ID}")
    assert response.status == 200, f"video host returned {response.status}"


@pytest.mark.regression
def test_unknown_path_returns_404(api):
    """A soft 200 on a missing page hides typos and broken links from every tool
    that looks for 404s, including search engines."""
    response = api.get("/no-such-page-xyz")
    assert response.status == 404, f"expected 404, got {response.status}"


@pytest.mark.regression
def test_sitemap_is_served(api):
    response = api.get("/sitemap.xml")
    assert response.status == 200
    assert "xml" in response.headers.get("content-type", "")
