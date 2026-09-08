import requests
import logging
import random
import string
from playwright.sync_api import expect

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BasePage:
    # Squarespace CDN prefix shared by every gallery image on the site.
    CDN_BASE = "https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537"

    def __init__(self, page):
        self.page = page

    def navigate(self, url):
        self.page.goto(url)
        expect(self.page).to_have_url(url)

    def check_title(self, title):
        expect(self.page).to_have_title(title)
    @staticmethod
    def generate_random_email():
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8)) + "@yopmail.com"

    @staticmethod
    def generate_random_phone_number():
        return '212' + ''.join(str(random.randint(0, 9)) for _ in range(7))

    def verify_gallery_images(self, image_paths):
        """Open the gallery lightbox and assert each expected image appears, in order.

        Assertion failures are deliberately allowed to propagate. Playwright's own
        message names the locator that failed, which a boolean return value loses.
        """
        self.page.locator(self._gallery_image_locator(image_paths[0])).first.click()
        for idx, path in enumerate(image_paths):
            expect(self.page.locator(self._gallery_image_locator(path)).first).to_be_visible()
            logging.info(f"Gallery image {idx + 1}/{len(image_paths)} visible: {path}")
            # Advance between images, but not past the last one: on short galleries
            # the arrow hides on the final image rather than wrapping around.
            if idx < len(image_paths) - 1:
                self.page.locator("a.sqs-lightbox-next").click()
        self.page.locator("a.sqs-lightbox-close").click()

    def _gallery_image_locator(self, image_path):
        return f"//img[@data-src='{self.CDN_BASE}/{image_path}']"

    def verify_embedded_video(self, video_id):
        """Check the page actually embeds the expected video, then that the embed loads.

        The DOM check is the part that tests the site: it fails if the video is
        removed from the page or swapped for a different one. The reachability
        check then confirms the video itself still resolves.
        """
        embed = self.page.locator(f"iframe[src*='{video_id}']").first
        expect(embed).to_be_attached(timeout=10000)
        src = embed.get_attribute("src")
        logging.info(f"Found embedded video {video_id} on {self.page.url}")
        return self.is_video_playing(src)

    def is_video_playing(self, video_url):
        response = requests.get(video_url)
        if response.status_code == 200:
            logging.info("The video loaded successfully (HTTP status code 200).")
            return True
        else:
            logging.error(f"The video did not load successfully. HTTP status code: {response.status_code}")
            return False
