import logging
import random
import string
import requests
from test_utility_basepage import BasePage
from playwright.sync_api import Playwright, sync_playwright, expect

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to generate a random 8-character alphanumeric email for yopmail.com
def generate_random_email():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(8)) + "@yopmail.com"

def generate_random_phone_number():
    prefix = '212'
    random_digits = ''.join(str(random.randint(0, 9)) for _ in range(7))
    return prefix + random_digits

# Home Page class
class HomePage(BasePage):
    HOME_URL = "https://thecmt.org/"

    def navigate_home(self):
        self.navigate(self.HOME_URL)

    def __init__(self, page):
        super().__init__(page)

    def go_to_auditorium(self):
        self.page.click("xpath=//a[@data-test='template-nav' and contains(text(),'Auditorium')]")
        logging.info("Navigated to Auditorium page")

# Auditorium Page class
class AuditoriumPage(BasePage):
    AUDITORIUM_URL = "https://thecmt.org/auditorium-2"

    def navigate_auditorium(self):
        self.navigate(self.AUDITORIUM_URL)

    def __init__(self, page):
        super().__init__(page)

    def check_video_playing(self):
        video_url = "https://www.youtube.com/embed/FzW2EzZcJVM"
        if self.is_video_playing(video_url):
            logging.info("The video on Auditorium Hall page is playing.")
        else:
            logging.error("The video on Auditorium Hall page is not playing.")

    def check_images_visible(self):
        try:
            # Verify visibility of each image as per the golden source
            images = [
                "1580823601655-JRS2CVG3WPBIUG8FY6FZ/CMT+HouseLeft.png",
                "1580823609276-Y5H8SMEVJRWJ6Z91ZB57/CMT-1.jpg",
                "1580823608663-GDNGOHPAF96PDT879LCI/CMT-2.jpg",
                "1580823621717-99MTYBPLTYRSTV6GWACT/CMT-3.jpg",
                "1580823615541-CGO8PEY11DRU5J78SNAK/CMT-4.jpg",
                "1580823620204-VY8PDGNGQTUE90ND8YD9/CMT-5.jpg",
                "1580823631675-4FVL7D8FZLBT1PYD49JH/CMT-6.jpg",
                "1580823630688-3E0QV4USL5XXKZWGUK3P/CMT-7.jpg",
                "1580823638406-59SBTHRQ49H4PJ8GB4MS/CMT-8.jpg",
                "1580823651688-CNFT9S1AAYJBIYOQZH14/CMT-9.jpg",
                "1580823660680-AOGALEXVUIXYIGBKCFHR/CMTBalcony.jpg",
                "1580823665857-2MEES7XARVDV4D3GGV5Q/CMT-Gateclose.jpg",
                "1580823669147-1EFTLBE7ZX3FWFDTGFA5/CMT-Gateclose2.jpg",
                "1580823669453-D4LGQOA1WCAP6RBI44L5/CMT-NYSBCornets.jpg",
                "1580823674896-TK2PZV33JH5N1K0MFCKH/cmt-rockband.png"
            ]


            self.page.locator('(//img[@alt="CMT HouseLeft.png"])').click()
            for image in images:
                expect(self.page.locator(f"//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/{image}']").first).to_be_visible()
                self.page.locator('//a[@aria-label="Next Item"]').click()

            self.page.locator("//a[@class='sqs-lightbox-close']").click()

            return True  # All images were successfully checked and visible

        except Exception as e:
            logging.error(f"An error occurred while checking images: {e}")
            return False  # An error occurred during the check


# Railton Hall Page class
class RailtonHallPage(BasePage):
    RAILTON_HALL_URL = "https://thecmt.org/railton-hall"

    def navigate_railton_hall(self):
        self.navigate(self.RAILTON_HALL_URL)
    def __init__(self, page):
        super().__init__(page)

    def check_video_playing(self):
        video_url = "https://www.youtube.com/embed/FzW2EzZcJVM"
        if self.is_video_playing(video_url):
            logging.info("The video on Railton Hall page is playing.")
        else:
            logging.error("The video on Railton Hall page is not playing.")

    def check_images_visible(self):
       try:
        # Implementation to check each image as per the golden source
        image_locators = [
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580812436962-WQW4G9LVZKXZD7RN1UXT/Railton+IMG_2905.jpg']",
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580812462938-G28VB6XMISVZRZ6P3WXA/Railton+IMG_2791.jpg']",
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580812518357-LLPZZ1TSS204VWX859VF/Railton+IMG_2886-2.jpg']",
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580812511400-MGUF6LDBXQKT3D1GS9MJ/Railton+IMG_2841.jpg']"
        ]

        for locator in image_locators:
            # Check if the locator is for the specific image
            if locator == "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580812436962-WQW4G9LVZKXZD7RN1UXT/Railton+IMG_2905.jpg']":
                self.page.click(locator)
                logging.info(f"Clicked on image at {locator}")

            expect(self.page.locator(locator).first).to_be_visible()
            logging.info(f"Image at {locator} is visible.")

            # Logic to click 'Next Item' for each image
            self.page.click('//a[@aria-label="Next Item"]')
                # Close the image viewer at the end
        self.page.click("//a[@class='sqs-lightbox-close']")

        return True  # All images were successfully checked and visible

       except Exception as e:
            logging.error(f"An error occurred while checking images: {e}")
            return False  # An error occurred during the check

# Mumford Hall Page class

class MumfordHallPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

    def navigate_mumford_hall(self):
        self.navigate("https://thecmt.org/new-index-1")
        expect(self.page).to_have_url("https://thecmt.org/new-index-1", timeout=7000)
        expect(self.page.locator("//h1[text()='Mumford Hall:']").first).to_have_text("Mumford Hall:", timeout=7000)

    def check_video_playing(self):
        video_url = "https://www.youtube.com/embed/FzW2EzZcJVM"
        if self.is_video_playing(video_url):
            logging.info("The video on Mumford Hall page is playing.")
        else:
            logging.error("The video on Mumford Hall page is not playing.")

    def check_images_visible(self):
       try:
        # Specific image locators as per the golden source
        image_locators = [
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580811977152-RKF5BQ8BT0UWYS1L8VLV/Mumford+Hall-IMG_3123-3.jpg']",
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580811980054-B1E3SKQ5UV9GDGWUEJF9/Mumford+Hall+-IMG_3156.jpg']",
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580812004277-JZT21BW5557412OLFZWQ/Mumford+Hall-IMG_3106-2.jpg']",
            "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580811988623-IN6JF6PCKVF1RFVJZJC2/Mumford-bkgd-IMG_5533.jpg']",
        ]

        for locator in image_locators:
            # Check if the locator is for the specific image
            if locator == "//img[@data-src='https://images.squarespace-cdn.com/content/v1/59676b47197aeab037427537/1580811977152-RKF5BQ8BT0UWYS1L8VLV/Mumford+Hall-IMG_3123-3.jpg']":
                self.page.click(locator)
                logging.info(f"Clicked on image at {locator}")

            expect(self.page.locator(locator).first).to_be_visible()
            logging.info(f"Image at {locator} is visible.")

            # Logic to click 'Next Item' for each image
            self.page.click('//a[@aria-label="Next Item"]')
                # Close the image viewer at the end
        self.page.click("//a[@class='sqs-lightbox-close']")

        return True  # All images were successfully checked and visible

       except Exception as e:
        logging.error(f"An error occurred while checking images: {e}")
        return False  # An error occurred during the check

# Usage in the test script
# ... Same as before ...

# Contact Page class
class ContactPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

    def navigate_and_verify(self):
        self.navigate("https://thecmt.org/new-index")
        expect(self.page).to_have_url("https://thecmt.org/new-index", timeout=7000)
        expect(self.page.locator("//h1[text()='Address: ']").first).to_have_text("Address: ", timeout=7000)

    def submit_contact_form(self, fname, lname, email, subject, message):
        self.page.fill('//input[@name="fname"]', fname)
        self.page.fill('//input[@name="lname"]', lname)
        self.page.fill('//input[@type="email"]', email)
        self.page.fill('//input[@type="text" and @autocomplete="false"]', subject)
        self.page.fill('//textarea[@aria-invalid="false"]', message)
        self.page.click('//button[@type="submit"]')
        #self.page.fill('//input[@autocomplete="tel-national"]', phone_number)


# 0 = {dict: 5} {'fname': '', 'lname': 'tester', 'email': 'random_email', 'subject': 'Test message', 'message': 'Hello'}
# 1 = {dict: 5} {'fname': 'Test', 'lname': '', 'email': 'random_email', 'subject': 'Test message', 'message': 'Hello'}
# 2 = {dict: 5} {'fname': 'Test', 'lname': 'tester', 'email': '', 'subject': 'Test message', 'message': 'Hello'}
# 3 = {dict: 5} {'fname': 'Test', 'lname': 'tester', 'email': 'random_email', 'subject': 'Test message', 'message': 'Hello'}
# 4 = {dict: 5} {'fname': 'Test', 'lname': 'tester', 'email': 'random@yopmail', 'subject': '', 'message': 'Hello'}
# 5 = {dict: 5} {'fname': 'Test', 'lname': 'tester', 'email': 'random@yopmail', 'subject': 'Test message', 'message': ''}

    def verify_all_fields_missing_failure(self):
        expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Name is required.')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Email is required.')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Subject is required.')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Message is required.')]").first).to_be_visible()
        logging.info("All fields all fields missing. Test passed.")


    def verify_missing_firstname_failure(self):
        #Index = 0
        expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'First Name is required')]").first).to_be_visible()
        logging.info("First name is missing first name. Test passed.")

    def verify_missing_lastname_failure(self):
        #Index = 1
        expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Last Name is required')]").first).to_be_visible()
        logging.info("Last name is missing last name. Test passed.")

    def verify_missing_email_failure(self):
        #Index = 2
        expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Email is required.')]").first).to_be_visible()
        logging.info("Email is missing email. Test passed.")

    def verify_incorrect_email_format_failure(self):
        #Index = 3
        expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Email is not valid. Email addresses should follow the format user@domain.com')]").first).to_be_visible()
        logging.info("Email is not in the correct format. Test passed.")

    # def verify_missing_failure(self):
    #     expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
    #     expect(self.page.locator("//p[contains(text(),'Name is required.')]").first).to_be_visible()
    #     expect(self.page.locator("//p[contains(text(),'Email is required.')]").first).to_be_visible()
    #     expect(self.page.locator("//p[contains(text(),'Subject is required.')]").first).to_be_visible()
    #     expect(self.page.locator("//p[contains(text(),'Message is required.')]").first).to_be_visible()
    #     logging.info("Message is missing. Test passed.")

    def verify_missing_subject(self):
        #Index = 4
        expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Subject is required.')]").first).to_be_visible()
        logging.info("Subject is missing subject. Test passed.")

    def verify_missing_message(self):
        #Index = 5
        expect(self.page.locator("//p[contains(text(),'Form submission failed. Review the following information:')]").first).to_be_visible()
        expect(self.page.locator("//p[contains(text(),'Message is required.')]").first).to_be_visible()
        logging.info("Message is missing message. Test passed.")


    def test_negative_scenarios(self):
        # Negative test all fields blank and submit
        self.page.reload()
        self.page.click('//button[@type="submit"]')
        self.verify_all_fields_missing_failure()

        # Negative tests for each individual field
        scenarios = [
            {'fname': '', 'lname': 'tester', 'email': 'wdqwd@yopmail.com', 'subject': 'Test message', 'message': 'Hello'},
            {'fname': 'Test', 'lname': '', 'email': 'qdqwdqwdqw@yopmail.com', 'subject': 'Test message', 'message': 'Hello'},
            {'fname': 'Test', 'lname': 'tester', 'email': '', 'subject': 'Test message', 'message': 'Hello'},
            {'fname': 'Test', 'lname': 'tester', 'email': 'ewfewfwefew', 'subject': 'Test message', 'message': 'Hello'},
            {'fname': 'Test', 'lname': 'tester', 'email': 'efwefwefwef@yopmail.com', 'subject': '', 'message': 'Hello'},
            {'fname': 'Test', 'lname': 'tester', 'email': 'wefefwfewef@yopmail.com', 'subject': 'Test message', 'message': ''}
        ]
        for scenario in scenarios:
            self.page.reload()
            self.submit_contact_form(**scenario)
            if scenarios.index(scenario) == 0:
                self.verify_missing_firstname_failure()
            elif scenarios.index(scenario) == 1:
                self.verify_missing_lastname_failure()
            elif scenarios.index(scenario) == 2:
                self.verify_missing_email_failure()
            elif scenarios.index(scenario) == 3:
                self.verify_incorrect_email_format_failure()
            elif scenarios.index(scenario) == 4:
                self.verify_missing_subject()
            elif scenarios.index(scenario) == 5:
                self.verify_missing_message()


    def test_positive_scenario(self, fname, lname, email, subject, message):
        self.page.reload()
        self.submit_contact_form(fname, lname, email, subject, message)
        expect(self.page.locator("//div[contains(text(),'Thank you!')]").first).to_have_text('Thank you!', timeout=7000)


