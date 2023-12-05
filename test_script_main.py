import logging
import pytest
from playwright.sync_api import sync_playwright
from test_utility_basepage import BasePage
from test_page_classes import HomePage, AuditoriumPage, RailtonHallPage, MumfordHallPage, ContactPage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@pytest.fixture(scope="session")
def playwright_browser():
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True, slow_mo=1000)
        yield browser
        browser.close()

@pytest.fixture(scope="session")
def playwright_context(playwright_browser):
    context = playwright_browser.new_context(record_video_dir='videos/')
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    context.tracing.stop()
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
        playwright_context.tracing.stop()

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
        playwright_context.tracing.stop()

@pytest.mark.regression
def test_auditorium_video(playwright_context):
    
    page = playwright_context.new_page()
    auditorium_page = AuditoriumPage(page)
    try:
        auditorium_page.navigate_auditorium()
        assert auditorium_page.is_video_playing("https://www.youtube.com/embed/FzW2EzZcJVM"), "Video did not load successfully"
    except Exception as e:
        page.screenshot(path='error_auditorium_video.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()

@pytest.mark.regression
def test_auditorium_images(playwright_context):
    
    page = playwright_context.new_page()
    auditorium_page = AuditoriumPage(page)
    try:
        auditorium_page.navigate_auditorium()
        assert auditorium_page.check_images_visible(), "Not all images are visible on the Auditorium page"
    except Exception as e:
        page.screenshot(path='error_auditorium_images.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()

@pytest.mark.smoke
@pytest.mark.regression
def test_railton_hall_video(playwright_context):
    
    page = playwright_context.new_page()
    railton_hall_page = RailtonHallPage(page)
    try:
        railton_hall_page.navigate_railton_hall()
        assert railton_hall_page.is_video_playing("https://www.youtube.com/embed/FzW2EzZcJVM"), "Video did not load successfully"
    except Exception as e:
        page.screenshot(path='error_railton_hall_video.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()

@pytest.mark.regression
def test_railton_hall_images(playwright_context):
    
    page = playwright_context.new_page()
    railton_hall_page = RailtonHallPage(page)
    try:
        railton_hall_page.navigate_railton_hall()
        assert railton_hall_page.check_images_visible(), "Not all images are visible on the Railton Hall page"
    except Exception as e:
        page.screenshot(path='error_railton_hall_images.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()

@pytest.mark.smoke
@pytest.mark.regression
def test_mumford_hall_video(playwright_context):
    
    page = playwright_context.new_page()
    mumford_hall_page = MumfordHallPage(page)
    try:
        mumford_hall_page.navigate_mumford_hall()
        assert mumford_hall_page.is_video_playing("https://www.youtube.com/embed/FzW2EzZcJVM"), "Video did not load successfully"
    except Exception as e:
        page.screenshot(path='error_mumford_hall_video.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()

@pytest.mark.regression
def test_mumford_hall_images(playwright_context):
    
    page = playwright_context.new_page()
    mumford_hall_page = MumfordHallPage(page)
    try:
        mumford_hall_page.navigate_mumford_hall()
        assert mumford_hall_page.check_images_visible(), "Not all images are visible on the Mumford Hall page"
    except Exception as e:
        page.screenshot(path='error_mumford_hall_images.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()

@pytest.mark.smoke
@pytest.mark.regression
def test_contact_page_positive(playwright_context):
    page = playwright_context.new_page()
    contact_page = ContactPage(page)
    try:
        contact_page.navigate_and_verify()
        base_page_instance = BasePage(page)
        random_email = base_page_instance.generate_random_email()
        contact_page.test_positive_scenario("Test", "User", random_email, "Test Inquiry", "This is a test message.")
    except Exception as e:
        page.screenshot(path='error_contact_page_positive.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()

@pytest.mark.regression
def test_contact_page_negative(playwright_context):
    page = playwright_context.new_page()
    contact_page = ContactPage(page)
    try:
        contact_page.navigate_and_verify()
        contact_page.test_negative_scenarios()
    except Exception as e:
        page.screenshot(path='error_contact_page_negative.png')
        raise e
    finally:
        page.close()
        playwright_context.tracing.stop()
