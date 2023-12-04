import requests
import logging
import random
import string
from playwright.sync_api import expect

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BasePage:
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

    def is_video_playing(self, video_url):
        response = requests.get(video_url)
        if response.status_code == 200:
            logging.info("The video loaded successfully (HTTP status code 200).")
            return True
        else:
            logging.error(f"The video did not load successfully. HTTP status code: {response.status_code}")
            return False
