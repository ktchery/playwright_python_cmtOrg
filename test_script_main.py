import logging
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright
from test_utility_basepage import BasePage
from test_page_classes import HomePage, AuditoriumPage, RailtonHallPage, MumfordHallPage, ContactPage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Absolute paths: Playwright resolves these against the driver process, not pytest's cwd.
ARTIFACT_DIR = Path(__file__).parent
VIDEO_DIR = ARTIFACT_DIR / "videos"
TRACE_PATH = ARTIFACT_DIR / "trace.zip"

# Headed with a 1s delay by default, so a human can watch the run. Set HEADLESS=1
# for CI or an unattended run; SLOW_MO overrides the per-action delay in ms.
HEADLESS = os.getenv("HEADLESS", "0").lower() not in ("0", "false", "")
SLOW_MO = int(os.getenv("SLOW_MO", "0" if HEADLESS else "1000"))


@pytest.fixture(scope="session")
def playwright_browser():
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def playwright_context(playwright_browser):
    context = playwright_browser.new_context(record_video_dir=str(VIDEO_DIR))
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    context.tracing.stop(path=str(TRACE_PATH))
    context.close()


@pytest.mark.smoke
@pytest.mark.regression
def test_home_page_title(playwright_context):
    
    page = playwright_context.new_page()
    home_page = HomePage(page)
    try:
        home_page.navigate_home()
        assert page.title() == "THECMT", "Title does not match expected value"
    except Exception as e:
        page.screenshot(path='error_home_page_title.png')
        raise e
    finally:
        page.close()

@pytest.mark.smoke
@pytest.mark.regression
def test_navigation_to_auditorium_page(playwright_context):
    
    page = playwright_context.new_page()
    auditorium_page = AuditoriumPage(page)
    try:
        auditorium_page.navigate_auditorium()
        assert page.url == "https://thecmt.org/auditorium-2", "URL does not match expected value"
    except Exception as e:
        page.screenshot(path='error_navigation_to_auditorium_page.png')
        raise e
    finally:
        page.close()

@pytest.mark.regression
def test_auditorium_video(playwright_context):
    
    page = playwright_context.new_page()
    auditorium_page = AuditoriumPage(page)
    try:
        auditorium_page.navigate_auditorium()
        assert auditorium_page.check_video_playing(), "Expected video is not embedded on the Auditorium page"
    except Exception as e:
        page.screenshot(path='error_auditorium_video.png')
        raise e
    finally:
        page.close()

@pytest.mark.regression
def test_auditorium_images(playwright_context):
    
    page = playwright_context.new_page()
    auditorium_page = AuditoriumPage(page)
    try:
        auditorium_page.navigate_auditorium()
        auditorium_page.check_images_visible()
    except Exception as e:
        page.screenshot(path='error_auditorium_images.png')
        raise e
    finally:
        page.close()

@pytest.mark.smoke
@pytest.mark.regression
def test_railton_hall_video(playwright_context):
    
    page = playwright_context.new_page()
    railton_hall_page = RailtonHallPage(page)
    try:
        railton_hall_page.navigate_railton_hall()
        assert railton_hall_page.check_video_playing(), "Expected video is not embedded on the Railton Hall page"
    except Exception as e:
        page.screenshot(path='error_railton_hall_video.png')
        raise e
    finally:
        page.close()

@pytest.mark.regression
def test_railton_hall_images(playwright_context):
    
    page = playwright_context.new_page()
    railton_hall_page = RailtonHallPage(page)
    try:
        railton_hall_page.navigate_railton_hall()
        railton_hall_page.check_images_visible()
    except Exception as e:
        page.screenshot(path='error_railton_hall_images.png')
        raise e
    finally:
        page.close()

@pytest.mark.smoke
@pytest.mark.regression
def test_mumford_hall_video(playwright_context):
    
    page = playwright_context.new_page()
    mumford_hall_page = MumfordHallPage(page)
    try:
        mumford_hall_page.navigate_mumford_hall()
        assert mumford_hall_page.check_video_playing(), "Expected video is not embedded on the Mumford Hall page"
    except Exception as e:
        page.screenshot(path='error_mumford_hall_video.png')
        raise e
    finally:
        page.close()

@pytest.mark.regression
def test_mumford_hall_images(playwright_context):
    
    page = playwright_context.new_page()
    mumford_hall_page = MumfordHallPage(page)
    try:
        mumford_hall_page.navigate_mumford_hall()
        mumford_hall_page.check_images_visible()
    except Exception as e:
        page.screenshot(path='error_mumford_hall_images.png')
        raise e
    finally:
        page.close()

@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.submits_real_form
def test_contact_page_positive(playwright_context):
    page = playwright_context.new_page()
    contact_page = ContactPage(page)
    try:
        contact_page.navigate_and_verify()
        base_page_instance = BasePage(page)
        random_email = base_page_instance.generate_random_email()
        random_phone = base_page_instance.generate_random_phone_number()
        contact_page.submit_valid_form("Test", "User", random_email, "Test Inquiry",
                                       "This is a test message.", phone=random_phone)
    except Exception as e:
        page.screenshot(path='error_contact_page_positive.png')
        raise e
    finally:
        page.close()

@pytest.mark.regression
@pytest.mark.submits_real_form
def test_contact_page_negative(playwright_context):
    page = playwright_context.new_page()
    contact_page = ContactPage(page)
    try:
        contact_page.navigate_and_verify()
        contact_page.run_negative_scenarios()
    except Exception as e:
        page.screenshot(path='error_contact_page_negative.png')
        raise e
    finally:
        page.close()
